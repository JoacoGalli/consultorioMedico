from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def enviar_email(subject, message, recipient_list, html_message=None):
    """Función genérica para enviar emails"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list if isinstance(recipient_list, list) else [recipient_list],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error al enviar email: {e}")
        return False


def enviar_confirmacion_turno(turno):
    """Envía email de confirmación de turno"""
    if not turno.paciente_email and not (turno.paciente and turno.paciente.user.email):
        return False

    email = turno.paciente_email or (turno.paciente.user.email if turno.paciente else None)
    if not email:
        return False

    nombre_paciente = (
        turno.paciente.user.get_full_name()
        if turno.paciente
        else f"{turno.paciente_apellido}, {turno.paciente_nombre}"
    )

    subject = (
        f"Turno confirmado - {turno.fecha.strftime('%d/%m/%Y')} {turno.hora.strftime('%H:%M')}"
    )

    message = f"""
Estimado/a {nombre_paciente},

Su turno ha sido confirmado exitosamente:

Médico: Dr. {turno.medico.nombre_completo}
Fecha: {turno.fecha.strftime("%d/%m/%Y")}
Hora: {turno.hora.strftime("%H:%M")}
Especialidad: {turno.medico.especialidad}

Recuerde llegar con 15 minutos de anticipación.

¿Necesita cancelar su turno? Por favor avise con al menos 24 horas de anticipación.

Saludos cordiales,
Consultorio Médico
"""

    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #2563eb; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9fafb; }}
        .turno-info {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✓ Turno Confirmado</h1>
        </div>
        <div class="content">
            <p>Estimado/a <strong>{nombre_paciente}</strong>,</p>
            <p>Su turno ha sido <strong>confirmado exitosamente</strong>.</p>
            
            <div class="turno-info">
                <p><strong>Médico:</strong> Dr. {turno.medico.nombre_completo}</p>
                <p><strong>Fecha:</strong> {turno.fecha.strftime("%d/%m/%Y")}</p>
                <p><strong>Hora:</strong> {turno.hora.strftime("%H:%M")}</p>
                <p><strong>Especialidad:</strong> {turno.medico.especialidad}</p>
            </div>
            
            <p><strong>Recordatorio:</strong> Por favor llegue con 15 minutos de anticipación.</p>
        </div>
        <div class="footer">
            <p>Consultorio Médico</p>
            <p>¿Necesita cancelar? Avise con al menos 24 horas de anticipación.</p>
        </div>
    </div>
</body>
</html>
"""

    return enviar_email(subject, message, email, html_message)


def enviar_cancelacion_turno(turno, motivo="Cancelación"):
    """Envía email de cancelación de turno"""
    email = turno.paciente_email or (turno.paciente.user.email if turno.paciente else None)
    if not email:
        return False

    nombre_paciente = (
        turno.paciente.user.get_full_name()
        if turno.paciente
        else f"{turno.paciente_apellido}, {turno.paciente_nombre}"
    )

    subject = f"Turno cancelado - {turno.fecha.strftime('%d/%m/%Y')} {turno.hora.strftime('%H:%M')}"

    message = f"""
Estimado/a {nombre_paciente},

Su turno ha sido <strong>cancelado</strong>.

Detalles del turno cancelado:
Médico: Dr. {turno.medico.nombre_completo}
Fecha: {turno.fecha.strftime("%d/%m/%Y")}
Hora: {turno.hora.strftime("%H:%M")}

Motivo: {motivo}

Si desea reprogramar su turno, puede hacerlo contactándose con el consultorio o a través de nuestro sistema online.

Saludos cordiales,
Consultorio Médico
"""

    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #dc2626; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9fafb; }}
        .turno-info {{ background-color: white; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #dc2626; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✗ Turno Cancelado</h1>
        </div>
        <div class="content">
            <p>Estimado/a <strong>{nombre_paciente}</strong>,</p>
            <p>Su turno ha sido <strong>cancelado</strong>.</p>
            
            <div class="turno-info">
                <p><strong>Médico:</strong> Dr. {turno.medico.nombre_completo}</p>
                <p><strong>Fecha:</strong> {turno.fecha.strftime("%d/%m/%Y")}</p>
                <p><strong>Hora:</strong> {turno.hora.strftime("%H:%M")}</p>
                <p><strong>Motivo:</strong> {motivo}</p>
            </div>
            
            <p>Si desea <strong>reprogramar</strong> su turno, puede:</p>
            <ul>
                <li>Contactarse directamente con el consultorio</li>
                <li>Reservar un nuevo turno a través de nuestro sistema online</li>
            </ul>
        </div>
        <div class="footer">
            <p>Consultorio Médico</p>
        </div>
    </div>
</body>
</html>
"""

    return enviar_email(subject, message, email, html_message)


def enviar_confirmacion_sobreturno(sobreturno):
    """Envía email de confirmación de sobreturno"""
    if not sobreturno.paciente_email:
        return False

    subject = f"Sobreturno confirmado - {sobreturno.fecha.strftime('%d/%m/%Y')} {sobreturno.hora.strftime('%H:%M')}"

    message = f"""
Estimado/a {sobreturno.paciente_apellido}, {sobreturno.paciente_nombre},

Su sobreturno ha sido confirmado.

Detalles:
Médico: Dr. {sobreturno.medico.nombre_completo}
Fecha: {sobreturno.fecha.strftime("%d/%m/%Y")}
Hora: {sobreturno.hora.strftime("%H:%M")}

Recuerde llegar con 10 minutos de anticipación.

Saludos,
Consultorio Médico
"""

    return enviar_email(subject, message, sobreturno.paciente_email)
