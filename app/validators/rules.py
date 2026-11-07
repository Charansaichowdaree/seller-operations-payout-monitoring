from decimal import Decimal

def payout_is_reconciled(header_total, line_totals, tolerance=Decimal('0.01')):
    return abs(Decimal(str(header_total))-sum((Decimal(str(x)) for x in line_totals),Decimal('0'))) <= tolerance

def payout_eligible(delivered_at, now, hold_days=7):
    return delivered_at is not None and now >= delivered_at + __import__('datetime').timedelta(days=hold_days)

def calculate_net(gross, commission_rate, refund=0, dispute=0, reserve_rate=Decimal('0.05')):
    gross=Decimal(str(gross)); commission=(gross*Decimal(str(commission_rate))).quantize(Decimal('0.01'))
    reserve=(gross*Decimal(str(reserve_rate))).quantize(Decimal('0.01'))
    net=max(Decimal('0.00'),gross-commission-Decimal(str(refund))-Decimal(str(dispute))-reserve)
    return {'gross':gross,'commission':commission,'refund':Decimal(str(refund)),'dispute':Decimal(str(dispute)),'reserve':reserve,'net':net}

def detect_double_commission(applied_commission, expected_commission, tolerance=Decimal('0.01')):
    return Decimal(str(applied_commission)) > Decimal(str(expected_commission))+tolerance
