from logger_setup import setup_logger
logger = setup_logger()

class PositionReconciler:
    def synchronize(self, broker, strategies):
        logger.info("--- Starting Position Reconciliation ---")
        order_book = broker.get_order_book()
        
        for strat in strategies:
            # 1. Look at all completed orders for this strategy's tag
            strat_orders = [o for o in order_book if o.get("tag") == strat.name and o.get("status") == "COMPLETE"]
            
            # 2. Calculate the True Broker Position
            true_position = sum(o["quantity"] if o["side"] == "BUY" else -o["quantity"] for o in strat_orders)
                
            # 3. Match against local state
            if strat.current_position != true_position:
                logger.warning(f"[{strat.name}] Local pos ({strat.current_position}) mismatch with Broker ({true_position}). Overriding local state!")
                strat.current_position = true_position
                
                # Save the corrected state immediately
                strat.state_manager.save_state(strat.name, {
                    "short_ema": strat.short_ema,
                    "long_ema": strat.long_ema,
                    "current_position": strat.current_position
                })
            else:
                logger.info(f"[{strat.name}] Perfectly reconciled at {true_position} units.")
                
        logger.info("--- Reconciliation Complete ---")
