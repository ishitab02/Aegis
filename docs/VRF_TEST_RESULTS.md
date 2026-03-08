# AEGIS VRF Test Results

## Deployment Transactions

### 1. VRF Consumer Deployment

- Transaction: Deployed via Foundry script
- Contract Address: `0x51bAC1448E5beC0E78B0408473296039A207255e`
- Block: 38526XXX
- BaseScan: [View Contract](https://sepolia.basescan.org/address/0x51bAC1448E5beC0E78B0408473296039A207255e)

### 2. Subscription Creation

- Transaction: `0x10001a8a7bf79cf30394c325e2140c3655f64abafb76dc9f3a488aff0c4329dd`
- Subscription ID: `11253994545520594848914204579213158096888562024819407235781468224794237415058`
- BaseScan: [View TX](https://sepolia.basescan.org/tx/0x10001a8a7bf79cf30394c325e2140c3655f64abafb76dc9f3a488aff0c4329dd)

### 3. Add Consumer to Subscription

- Transaction: `0x732ef996f6135ef905425063c7986e60e445e02dd70144fb604f8679b8f60a49`
- Consumer: `0x51bAC1448E5beC0E78B0408473296039A207255e`
- BaseScan: [View TX](https://sepolia.basescan.org/tx/0x732ef996f6135ef905425063c7986e60e445e02dd70144fb604f8679b8f60a49)

### 4. Set Subscription ID on Consumer

- Transaction: `0x65f9f9d0f9f4dc7e94c747301fdbca9016f7db8bf5158f63ffb4d71c0a7c6443`
- BaseScan: [View TX](https://sepolia.basescan.org/tx/0x65f9f9d0f9f4dc7e94c747301fdbca9016f7db8bf5158f63ffb4d71c0a7c6443)

### 5. Fund Subscription with LINK

- Transaction: `0x874d56d6b44f3f33d3451098bc468cbafec7f7473334cfdde3515afd2b5017ef`
- Amount: 2 LINK
- BaseScan: [View TX](https://sepolia.basescan.org/tx/0x874d56d6b44f3f33d3451098bc468cbafec7f7473334cfdde3515afd2b5017ef)

## VRF Request Test

### Request Details

- Request Transaction: `0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff`
- Request ID: `105854781675887753695428977360749468429975281596141840240373046955913436167727`
- Request ID (hex): `0xea07aee8b801501e59f9461fdc985e02fb622984ccded3689e498276372b7e2f`
- Tie-Breaker ID: `1`
- Sentinel Options: `[1, 2, 3]`
- Block Number: `38526458`
- BaseScan: [View TX](https://sepolia.basescan.org/tx/0x761cb3637348d7064ec5b56a332988fc1828603fd5cf2e91325af38c1f4e45ff)

### Fulfillment Status

To check fulfillment status:

```bash
# Check if fulfilled
cast call 0x51bAC1448E5beC0E78B0408473296039A207255e \
  "isRequestFulfilled(uint256)(bool)" \
  105854781675887753695428977360749468429975281596141840240373046955913436167727 \
  --rpc-url https://sepolia.base.org

# Get result (once fulfilled)
cast call 0x51bAC1448E5beC0E78B0408473296039A207255e \
  "getLastSelectedSentinel()(uint256)" \
  --rpc-url https://sepolia.base.org
```
