"""Portfolio template service."""
import logging
import uuid
from typing import List, Optional, Dict, Any
from app.database import get_supabase

logger = logging.getLogger(__name__)


def get_all_templates() -> List[Dict[str, Any]]:
    """Get all available portfolio templates."""
    try:
        sb = get_supabase()
        # Query directly from portfolio_templates table instead of view
        # to avoid potential RLS issues with views
        templates_res = (
            sb.table("portfolio_templates")
            .select("id, name, description, display_order")
            .eq("is_active", True)
            .order("display_order", desc=False)
            .execute()
        )
        
        if not templates_res.data:
            logger.warning("No active templates found")
            return []
        
        templates = []
        for template in templates_res.data:
            template_dict = {
                "template_id": template.get("id"),
                "template_name": template.get("name"),
                "description": template.get("description"),
                "display_order": template.get("display_order"),
            }
            templates.append(template_dict)
        
        logger.info(f"Retrieved {len(templates)} active templates")
        return templates
    except Exception as e:
        logger.error(f"Failed to get templates: {str(e)}", exc_info=True)
        return []


def copy_template_to_user(user_id: str, template_id: str, portfolio_name: Optional[str] = None) -> str:
    """Copy a template to user's portfolio."""
    try:
        sb = get_supabase()
        
        # Get template
        template_res = sb.table("portfolio_templates").select("*").eq("id", template_id).execute()
        if not template_res.data:
            raise ValueError(f"Template not found")
        
        template = template_res.data[0]
        template_name = portfolio_name or template["name"]
        
        # Get template items
        items_res = (
            sb.table("portfolio_template_items")
            .select("*")
            .eq("template_id", template_id)
            .order("display_order", desc=False)
            .execute()
        )
        
        template_items = items_res.data or []
        if not template_items:
            raise ValueError("Template has no items")
        
        # Create portfolio
        new_portfolio_id = str(uuid.uuid4())
        portfolio_data = {
            "id": new_portfolio_id,
            "user_id": user_id,
            "name": template_name,
            "portfolio_type": "template",
            "initial_amount": 100000
        }
        
        port_res = sb.table("backtest_portfolios").insert(portfolio_data).execute()
        if not port_res.data:
            raise Exception("Failed to create portfolio")
        
        # Add items
        items_to_insert = [
            {
                "portfolio_id": new_portfolio_id,
                "symbol": item["symbol"],
                "name": item.get("name", item["symbol"]),
                "weight": item["weight"],
                "category": "index"
            }
            for item in template_items
        ]
        
        items_res = sb.table("backtest_portfolio_items").insert(items_to_insert).execute()
        if not items_res.data:
            sb.table("backtest_portfolios").delete().eq("id", new_portfolio_id).execute()
            raise Exception("Failed to insert items")
        
        logger.info(f"Copied template to portfolio {new_portfolio_id}")
        return new_portfolio_id
        
    except Exception as e:
        logger.error(f"Failed to copy template: {str(e)}", exc_info=True)
        raise


def init_user_default_portfolios(user_id: str) -> List[str]:
    """Initialize default portfolios for new user."""
    try:
        logger.info(f"Initializing portfolios for user {user_id}")
        templates_data = get_all_templates()
        
        if not templates_data:
            logger.warning(f"No templates found to initialize for user {user_id}")
            return []
        
        created_portfolio_ids = []
        
        for template_data in templates_data:
            try:
                template_id = template_data.get("template_id")
                if not template_id:
                    logger.warning(f"Template has no ID: {template_data}")
                    continue
                
                logger.info(f"Creating portfolio from template {template_id} for user {user_id}")
                portfolio_id = copy_template_to_user(user_id=user_id, template_id=template_id)
                created_portfolio_ids.append(portfolio_id)
                logger.info(f"Successfully created portfolio {portfolio_id}")
                
            except Exception as e:
                logger.error(f"Failed to create portfolio from template {template_data.get('template_id')}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"Initialized {len(created_portfolio_ids)} portfolios for user {user_id}")
        return created_portfolio_ids
        
    except Exception as e:
        logger.error(f"Failed to initialize portfolios for user {user_id}: {str(e)}", exc_info=True)
        return []
