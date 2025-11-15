from typing import List
from app.models.asset import Asset
from app.models.brand import Brand
from app.models.campaign import Campaign

class CheckResult:
    """A simple container for check results."""
    
    def __init__(self, check_type: str, result: str, details: dict = {}):
        self.check_type = check_type
        self.result = result
        self.details = details or {}

    def __repr__(self) -> str:
        return f"CheckResult(check_type={self.check_type}, result={self.result})"

def run_brand_checks(asset: Asset, brand: Brand, img) -> List[CheckResult]:
    """
    Runs basic brand compliance checks on the generated asset.
    Checks if the brand's logo and colors are used correctly in the generated image.
    """
    checks: List[CheckResult] = []
    
    # Check logo presence in the image
    # For the POC, we assume that if the logo is in the asset, it's considered a pass
    logo_check = "PASS" if asset.s3_key and asset.s3_key.endswith(brand.logo_filename) else "FAIL"
    checks.append(CheckResult(check_type="LOGO", result=logo_check, details={"logo_present": logo_check == "PASS"}))
    
    # Check if the brand colors are in the image (simplified for POC)
    # Assume brand's primary and secondary colors should be dominant in the image
    primary_color_check = "PASS" if brand.primary_color in img else "FAIL"
    checks.append(CheckResult(check_type="COLOR", result=primary_color_check, details={"primary_color": primary_color_check}))
    
    return checks

def run_legal_checks(campaign: Campaign, brand: Brand) -> List[CheckResult]:
    """
    Runs basic legal checks on the campaign message and any additional disclaimers or text.
    Checks if the campaign message follows legal guidelines (e.g., banned words).
    """
    checks: List[CheckResult] = []
    
    banned_words = ["guaranteed", "cure", "100% safe"]  # Example banned phrases
    message = campaign.campaign_message.lower()
    
    for word in banned_words:
        if word in message:
            checks.append(CheckResult(check_type="LEGAL", result="FAIL", details={"banned_word": word}))
        else:
            checks.append(CheckResult(check_type="LEGAL", result="PASS"))
    
    return checks
