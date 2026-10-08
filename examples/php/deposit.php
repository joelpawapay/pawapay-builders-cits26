<?php
// Collect a mobile money payment (a deposit) on the pawaPay sandbox.
// PHP 7.4+ with the curl extension. No Composer packages needed.
//
// Run from the examples/ folder:
//   php php/deposit.php [phoneNumber] [amount]
//   php php/deposit.php 237653456789 1000

// Load .env from the current folder.
if (file_exists('.env')) {
    foreach (file('.env', FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        if ($line[0] === '#' || strpos($line, '=') === false) continue;
        [$key, $value] = array_map('trim', explode('=', $line, 2));
        if (getenv($key) === false) putenv("$key=$value");
    }
}

$token = getenv('PAWAPAY_API_TOKEN') ?: '';
$baseUrl = getenv('PAWAPAY_BASE_URL') ?: 'https://api.sandbox.pawapay.io';
$team = getenv('PAWAPAY_TEAM') ?: 'team-unknown';

if ($token === '' || strpos($token, 'paste-') === 0) {
    fwrite(STDERR, "Set PAWAPAY_API_TOKEN in examples/.env first. See getting-started.md.\n");
    exit(1);
}

function stop(string $message): void
{
    fwrite(STDERR, "pawaPay said: $message\n");
    if (preg_match('/AUTHENTICATION|AUTHORISATION/', $message)) {
        fwrite(STDERR, "Check PAWAPAY_API_TOKEN in examples/.env. It must be a sandbox token.\n");
    }
    exit(1);
}

function pawapay(string $method, string $path, ?array $body = null): array
{
    global $token, $baseUrl;
    $curl = curl_init($baseUrl . $path);
    curl_setopt_array($curl, [
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_HTTPHEADER => ["Authorization: Bearer $token", 'Content-Type: application/json'],
    ]);
    if ($body !== null) curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode($body));
    $raw = curl_exec($curl);
    if ($raw === false) stop('network error: ' . curl_error($curl));
    $httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    $data = json_decode($raw, true) ?? [];
    if (!empty($data['failureReason'])) {
        $reason = $data['failureReason'];
        stop("{$reason['failureCode']}: {$reason['failureMessage']}");
    }
    if ($httpCode >= 400) stop("HTTP $httpCode: $raw");
    return $data;
}

function uuidv4(): string
{
    $bytes = random_bytes(16);
    $bytes[6] = chr((ord($bytes[6]) & 0x0f) | 0x40);
    $bytes[8] = chr((ord($bytes[8]) & 0x3f) | 0x80);
    return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($bytes), 4));
}

$phoneInput = $argv[1] ?? '237653456789';
$amount = $argv[2] ?? '1000';

// 1. Clean up the phone number and find out which operator it belongs to.
$predicted = pawapay('POST', '/v2/predict-provider', ['phoneNumber' => $phoneInput]);
echo "Phone {$predicted['phoneNumber']} is on {$predicted['provider']}\n";

// 2. Create the deposit ID yourself. In a real app, save it to your database now.
$depositId = uuidv4();

// 3. Ask pawaPay to collect the money.
$initiated = pawapay('POST', '/v2/deposits', [
    'depositId' => $depositId,
    'amount' => (string) $amount, // a string, never a number. XAF has no decimals.
    'currency' => 'XAF',
    'payer' => [
        'type' => 'MMO',
        'accountDetails' => [
            'phoneNumber' => $predicted['phoneNumber'],
            'provider' => $predicted['provider'],
        ],
    ],
    'customerMessage' => 'CITS26 test',
    'metadata' => [['team' => $team]],
]);
echo "Deposit $depositId: {$initiated['status']}\n";
if ($initiated['status'] !== 'ACCEPTED') exit(1);

// 4. ACCEPTED is not paid. Poll until the deposit reaches COMPLETED or FAILED.
for ($attempt = 1; $attempt <= 20; $attempt++) {
    sleep(3);
    $check = pawapay('GET', "/v2/deposits/$depositId");
    $status = $check['status'] === 'FOUND' ? $check['data']['status'] : $check['status'];
    echo "  check $attempt: $status\n";

    if ($status === 'COMPLETED') {
        echo "Payment received. Deliver the goods.\n";
        exit(0);
    }
    if ($status === 'FAILED') {
        $reason = $check['data']['failureReason'] ?? [];
        echo "Payment failed: " . ($reason['failureCode'] ?? '') . " (" . ($reason['failureMessage'] ?? '') . ")\n";
        exit(1);
    }
}
echo "Still pending after 60 seconds. Check again later with the deposit ID above.\n";
