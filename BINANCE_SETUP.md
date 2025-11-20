# Binance API Setup Guide

This guide shows how to set up and run the Binance MCP server with proper authentication.

## Authentication

Binance uses **API Key + Secret** authentication with HMAC SHA256 signatures:
- **API Key**: Sent in `X-MBX-APIKEY` header
- **API Secret**: Used to sign requests with HMAC SHA256
- **Timestamp**: Added automatically to prevent replay attacks
- **Signature**: HMAC SHA256 hash of query parameters

## Getting Binance API Credentials

1. Go to [Binance](https://www.binance.com/) and log in
2. Navigate to **API Management** (Account → API Management)
3. Create a new API key
4. Save your **API Key** and **Secret Key** securely
5. Configure API restrictions (IP whitelist, permissions, etc.)

## Running the Server

### Option 1: Simple Server (Recommended)

The simple server regenerates tools on startup. You can provide credentials in two ways:

#### Method A: Using Environment Variables

```bash
# For public endpoints only (no authentication)
python run_binance_simple.py

# For authenticated endpoints
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_secret_key_here"
python run_binance_simple.py
```

#### Method B: Using Config File (Easier for Development)

```bash
# Copy the example config file
cp binance_config.json.example binance_config.json

# Edit the config file with your credentials
nano binance_config.json
# or
vim binance_config.json

# Run the server (credentials loaded automatically)
python run_binance_simple.py
```

**Config file format** (`binance_config.json`):
```json
{
  "api_key": "your_binance_api_key_here",
  "api_secret": "your_binance_api_secret_here",
  "base_url": "https://api.binance.com",
  "recv_window": 5000
}
```

**Priority**: Environment variables take precedence over config file. This allows you to override config file settings when needed.

### Option 2: Pre-generated Registry Server

The registry server uses cached tools for faster startup. Same credential options as Option 1:

```bash
# Step 1: Generate the registry (run once)
python generate_binance_registry.py

# Step 2: Run the server

# Method A: Using environment variables
export BINANCE_API_KEY="your_api_key_here"
export BINANCE_API_SECRET="your_secret_key_here"
python run_binance_server.py

# Method B: Using config file (create binance_config.json first)
python run_binance_server.py
```

## Public vs Authenticated Endpoints

### Public Endpoints (No API Key Required)
- Market data (ticker, orderbook, trades, klines)
- Exchange information
- System status

Examples:
- `GET /api/v3/ticker/24hr` - 24hr ticker price change
- `GET /api/v3/depth` - Order book depth
- `GET /api/v3/klines` - Kline/candlestick data

### Authenticated Endpoints (API Key + Secret Required)
- Account information
- Order placement/cancellation
- Trade history
- Wallet operations

Examples:
- `GET /api/v3/account` - Account information
- `POST /api/v3/order` - Place new order
- `DELETE /api/v3/order` - Cancel order
- `GET /api/v3/myTrades` - Get trades

## Security Best Practices

1. **Never commit credentials** to version control
   - `binance_config.json` is in `.gitignore` - it will NOT be committed
   - Only `binance_config.json.example` (without real credentials) is tracked
2. **Choose the right credential method**:
   - **Config file** (`binance_config.json`): Good for local development
   - **Environment variables**: Better for production/containers/CI
3. **Restrict API permissions** on Binance:
   - Enable only needed permissions (read, trade, withdraw)
   - Set IP whitelist if possible
   - Enable 2FA on your Binance account
4. **Rotate keys regularly**
5. **Monitor API usage** in Binance dashboard
6. **File permissions** (if using config file):
   ```bash
   chmod 600 binance_config.json  # Only you can read/write
   ```

## Testing the Setup

Test with a public endpoint (no auth needed):

```bash
# This should work without credentials
curl https://api.binance.com/api/v3/ping
```

Test with authenticated endpoint:

```bash
# Option 1: Using environment variables
export BINANCE_API_KEY="your_api_key"
export BINANCE_API_SECRET="your_secret"
python run_binance_simple.py

# Option 2: Using config file
cp binance_config.json.example binance_config.json
# Edit binance_config.json with your credentials
python run_binance_simple.py

# The server will show one of:
# ✓ Loaded credentials from environment variables
#   Auth: Authenticated (API Key + HMAC SHA256)
# OR
# ✓ Loaded credentials from binance_config.json
#   Auth: Authenticated (API Key + HMAC SHA256)
```

## API Rate Limits

Binance has rate limits:
- **Weight-based limits**: Each endpoint has a weight (1-100)
- **Order limits**: Separate limits for order placement
- **IP limits**: Limits per IP address

The server automatically adds timestamps and signatures, but does **not** implement rate limiting. Monitor your usage to avoid bans.

## Troubleshooting

### "String should have at most 64 characters" (Tool Name Limit)
- **Cause**: Claude's MCP protocol limits tool names to 64 characters
- **Solution**: The adapter automatically truncates long names by removing version numbers (v1, v2, v3) and API keywords (api, sapi)
- **Note**: Some Binance endpoints have very long paths. The adapter intelligently shortens these while preserving readability
- **Example**:
  - Original: `binance_delete_sapi_v1_sub_account_sub_account_api_ip_restriction_ip_list` (73 chars)
  - Truncated: `binance_delete_sub_account_sub_account_ip_restriction_ip_list` (64 chars)

### "Timestamp for this request is outside of the recvWindow"
- Your system clock is not synchronized
- Solution: Sync your system time with NTP

### "Invalid API-key, IP, or permissions for action"
- Check your API key is correct
- Verify IP whitelist settings on Binance
- Ensure API has required permissions

### "Signature for this request is not valid"
- Check your API secret is correct
- Ensure parameters are being sorted correctly
- Verify timestamp is being added

## Reference

- [Binance API Documentation](https://binance-docs.github.io/apidocs/spot/en/)
- [Binance API Postman Collection](https://github.com/binance/binance-api-postman)
- [Binance Spot API Swagger](https://github.com/binance/binance-api-swagger)
