# app/utils/crud_helpers.py

def get_or_404(model, **kwargs):
    """Récupère une entité ou renvoie une 404"""
    result = model.query.filter_by(**kwargs).first()
    if not result:
        abort(404)
    return result

def save_form_data(form, model_instance, flash_message=None, **additional_fields):
    """Sauvegarde les données d'un formulaire dans une instance de modèle"""
    try:
        for key, value in form.items():
            if hasattr(model_instance, key):
                setattr(model_instance, key, value)
        
        for key, value in additional_fields.items():
            setattr(model_instance, key, value)
            
        db.session.add(model_instance)
        db.session.commit()
        
        if flash_message:
            flash(flash_message, "success")
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'enregistrement : {str(e)}", "error")
        return False

def delete_entity(model_instance, flash_message=None):
    """Supprime une entité de la base de données"""
    try:
        db.session.delete(model_instance)
        db.session.commit()
        if flash_message:
            flash(flash_message, "success")
        return True
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression : {str(e)}", "error")
        return False
