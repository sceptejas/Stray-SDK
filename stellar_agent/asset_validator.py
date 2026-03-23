from stellar_sdk import Server

class AssetValidator:
    """
    Stray-SDK Asset Validator module.
    Checks if an account has a valid trustline for a specific asset.
    """
    def __init__(self, horizon_url="https://horizon-testnet.stellar.org"):
        self.server = Server(horizon_url)

    def check_trustline(self, public_key, asset_code, asset_issuer):
        try:
            account_info = self.server.accounts().account_id(public_key).call()
            balances = account_info.get('balances', [])
            
            for balance in balances:
                if balance.get('asset_code') == asset_code and balance.get('asset_issuer') == asset_issuer:
                    return {
                        "exists": True,
                        "limit": balance.get('limit'),
                        "balance": balance.get('balance')
                    }
            return {"exists": False, "message": "Trustline not found for this asset."}
        except Exception as e:
            return {"error": str(e)}

# Bu modül ajanın belirli bir varlığı alıp alamayacağını önceden kontrol etmesini sağlar.
