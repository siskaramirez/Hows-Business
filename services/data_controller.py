import flet as ft

class TransactionController:
    def __init__(self):
        self.transactions = [
            {"id": "01", "date": "05/25/2026", "account_name": "Product Sales", "status": "active", "description": "Morning Bread Batch", "ref_no": "INV-000001", "amount": 4200.00},
            {"id": "02", "date": "05/25/2026", "account_name": "Utilities", "status": "active", "description": "LPG Refill - Morning", "ref_no": "INV-000002", "amount": 1200.00},
            {"id": "03", "date": "05/25/2026", "account_name": "Product Sales", "status": "edit", "description": "Afternoon batch - Rice Meal", "ref_no": "INV-000003", "amount": 2500.00},
            {"id": "04", "date": "05/26/2026", "account_name": "Product Sales", "status": "active", "description": "Edited: Afternoon batch - Rice Meal", "ref_no": "INV-000004", "amount": 3100.00},
            {"id": "05", "date": "05/26/2026", "account_name": "Product Sales", "status": "void", "description": "Wrong Rice Meal Ordered", "ref_no": "INV-000005", "amount": 900.00},
        ]

    def get_all(self):
        return self.transactions

    def add_record(self, date, description, account_name, amount, payment_method, tx_type, invoice_no):
        next_id = f"{len(self.transactions) + 1:02d}"
        
        new_tx = {
            "id": next_id,
            "date": date,
            "account_name": account_name,
            "status": "active",
            "description": f"{tx_type} ({payment_method}) - {description}",
            "ref_no": invoice_no if invoice_no else f"TXT-{next_id}00",
            "amount": float(amount.replace(",", "")) if isinstance(amount, str) else float(amount)
        }
        self.transactions.insert(0, new_tx)
        return new_tx
        
db_controller = TransactionController()