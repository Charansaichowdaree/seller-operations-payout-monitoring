from datetime import datetime,timedelta,timezone
from decimal import Decimal
from app.validators.rules import payout_is_reconciled,payout_eligible,calculate_net,detect_double_commission

def test_payout_reconciles(): assert payout_is_reconciled('100.00',['40.00','60.00'])
def test_payout_mismatch_detected(): assert not payout_is_reconciled('101.00',['40.00','60.00'])
def test_hold_window():
 d=datetime(2026,1,1,tzinfo=timezone.utc)
 assert not payout_eligible(d,d+timedelta(days=6))
 assert payout_eligible(d,d+timedelta(days=7))
def test_commission_and_reserve_math():
 x=calculate_net('10000','0.10','500','300','0.05')
 assert x['commission']==Decimal('1000.00') and x['reserve']==Decimal('500.00') and x['net']==Decimal('7700.00')
def test_double_commission(): assert detect_double_commission('20','10')
