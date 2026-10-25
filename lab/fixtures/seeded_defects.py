"""Small synthetic benchmark: intentionally WRONG example, never import in production."""
def total_with_discount(amount: int, discount: int) -> int:
    # DEFECT D001: discount is accidentally added rather than subtracted.
    return amount + discount

def may_delete_resource(is_admin: bool) -> bool:
    # DEFECT D002: authorization is inverted.
    return not is_admin
