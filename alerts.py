from database import db
from market import get_gift_price


class AlertManager:
    async def check_alerts(self):
        """Проверить все активные алерты и вернуть сработавшие"""
        alerts = await db.get_all_active_alerts()
        triggered = []

        for alert in alerts:
            try:
                current_price = await get_gift_price(alert['gift_name'])
                
                condition_met = False
                if alert['condition'] == 'ниже' and current_price <= alert['price']:
                    condition_met = True
                elif alert['condition'] == 'выше' and current_price >= alert['price']:
                    condition_met = True

                if condition_met:
                    await db.deactivate_alert(alert['id'])
                    triggered.append({
                        'user_id': alert['user_id'],
                        'gift_name': alert['gift_name'],
                        'condition': alert['condition'],
                        'target_price': alert['price'],
                        'current_price': round(current_price, 2),
                    })
            except Exception:
                continue

        return triggered


alert_manager = AlertManager()
