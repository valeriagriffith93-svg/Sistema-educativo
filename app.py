from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer as Serializer
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Clave secreta para sesiones
app.secret_key = "advpjsh"

UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de MongoDB Atlas
client = MongoClient("mongodb+srv://vale:vale2026Mongo@usuarios.1ncbu1v.mongodb.net/?appName=Usuarios")
db = client['db1'] #Nombre de tu base de datos aquí
collection = db['usuarios'] #Nombre de tu colección aquí
asistencias_collection = db['asistencias']
tareas_collction = db['tareas']
entregas_collction = db['entregas']

# Configuración de SendGrid
SENDGRID_API_KEY = ''

# Serializador para crear y verificar tokens
serializer = Serializer(app.secret_key, salt='password-reset-salt')

# Función para enviar correos
def enviar_email(destinatario, asunto, cuerpo):
    mensaje = Mail(
        from_email='valeria9griffith@gmail.com',  # Cambia esto por tu correo
        to_emails=destinatario,
        subject=asunto,
        html_content=cuerpo
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)  # Usa tu clave API de SendGrid directamente
        response = sg.send(mensaje)
        print(f"Correo enviado con éxito! Status code: {response.status_code}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

@app.route('/')
def home():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('pagina_principal'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']
        contrasena = request.form['contrasena']
        direccion = request.form['direccion']
        rol = request.form['rol']
        grupo = request.form.get('grupo', '')

        # Verificar si el correo ya está registrado
        if collection.find_one({'email': email}):
            flash("El correo electrónico ya está registrado.")
            return redirect(url_for('registro'))

        # Hashear la contraseña
        hashed_password = bcrypt.generate_password_hash(contrasena).decode('utf-8')

        # Insertar usuario en la base de datos
        collection.insert_one({
            'usuario': usuario,
            'email': email,
            'contrasena': hashed_password,
            'direccion' : direccion,
            'rol': rol,
            'grupo': grupo
        })
        
        session['usuario'] = usuario
        session['rol'] = rol
        return redirect(url_for('pagina_principal'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        rol = request.form['rol']

        # Buscar al usuario en la base de datos
        user = collection.find_one({'usuario': usuario})
        
        # Verificar si las credenciales son correctas
        if user and bcrypt.check_password_hash(user['contrasena'], contrasena):

            if user['rol'] != rol:
                flash(f"Esta cuenta pertenece a un {user['rol']}.")
                return render_template('login.html')
            
            session['usuario'] = usuario
            session['rol'] = rol
            return redirect(url_for('pagina_principal'))
        else:
            flash("Usuario o contraseña incorrectos.")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/pagina_principal')
def pagina_principal():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if session['rol'] == 'profesor':
        return render_template(
            'inicio_profesor.html',
            usuario=session['usuario']
        )
    return render_template(
        'inicio_estudiante.html',
        usuario=session['usuario']
    )

@app.route('/asistencias', methods=['GET', 'POST'])
def asistencias():

    if request.method == 'POST':

        grupo = request.form['grupo']
        fecha = request.form['fecha']

        estudiantes = collection.find({
            'rol': 'estudiante',
            'grupo': grupo
        })

        for estudiante in estudiantes:

            estado = request.form.get(
                f"asistencia_{estudiante['usuario']}"
            )

            asistencias_collection.insert_one({
                'usuario': estudiante['usuario'],
                'correo': estudiante['email'],
                'grupo': grupo,
                'fecha': fecha,
                'estado': estado
            })

        flash("Asistencias guardadas correctamente")

        return redirect(
            url_for(
                'asistencias',
                grupo=grupo,
                fecha=fecha
            )
        )

    grupo = request.args.get('grupo')
    fecha = request.args.get('fecha')

    estudiantes = []

    if grupo:
        estudiantes = collection.find({
            'rol': 'estudiante',
            'grupo': grupo
        })

    return render_template(
        'asistencias.html',
        estudiantes=estudiantes,
        grupo=grupo,
        fecha=fecha
    )

@app.route('/historial')
def historial():

    fecha = request.args.get('fecha')

    if fecha:
        historial = asistencias_collection.find({
            'fecha': fecha
        })

    else:
        historial = asistencias_collection.find()

    grupo1001 = asistencias_collection.find({'grupo': '1001'})
    grupo1002 = asistencias_collection.find({'grupo': '1002'})
    grupo1003 = asistencias_collection.find({'grupo': '1003'})
    grupo1004 = asistencias_collection.find({'grupo': '1004'})

    grupo1101 = asistencias_collection.find({'grupo': '1101'})
    grupo1102 = asistencias_collection.find({'grupo': '1102'})
    grupo1103 = asistencias_collection.find({'grupo': '1103'})
    grupo1104 = asistencias_collection.find({'grupo': '1104'})

    return render_template(
        'historial.html',
        grupo1001=grupo1001,
        grupo1002=grupo1002,
        grupo1003=grupo1003,
        grupo1004=grupo1004,
        grupo1101=grupo1101,
        grupo1102=grupo1102,
        grupo1103=grupo1103,
        grupo1104=grupo1104,
        historial=historial
    )
    
@app.route('/eliminar_asistencia/<id>')
def eliminar_asistencia(id):
     asistencias_collection.delete_one({
         '_id': ObjectId(id)
     })

     flash("Asistencia eliminada correctamente")

     return redirect(url_for('historial'))

@app.route('/editar_asistencia/<id>', methods=['GET', 'POST'])
def editar_asistencia(id):

    asistencia = asistencias_collection.find_one({
        '_id': ObjectId(id)
    })

    if request.method == 'POST':

        nuevo_estado = request.form['estado']

        asistencias_collection.update_one(
            {'_id': ObjectId(id)},
            {
                '$set':{
                    'estado': nuevo_estado
                }
            }
        )

        flash("Asistencia actualizada")

        return redirect(url_for('historial'))
    return render_template(
        'editar_asistencia.html',
        asistencia=asistencia
    )

@app.route('/estadisticas')
def estadisticas():

    total = asistencias_collection.count_documents({})

    asistieron = asistencias_collection.count_documents({
        'estado': 'si'
    })

    faltaron = asistencias_collection.count_documents({
        'estado': 'no'
    })

    porcentaje_asistencia = round(
        (asistieron / total) * 100,
        2
    ) if total > 0 else 0

    estudiantes = collection.find({
        'rol': 'estudiante'
    })

    resumen = []

    for estudiante in estudiantes:

        total_est = asistencias_collection.count_documents({
            'usuario' : estudiante['usuario']
        })

        asistio_est = asistencias_collection.count_documents({
            'usuario': estudiante['usuario'],
            'estado':'si'
        })

        falto_est = asistencias_collection.count_documents({
            'usuario': estudiante['usuario'],
            'estado': 'no'
        })

        porcentaje_est = round(
            (asistio_est / total_est) * 100,
            2
        ) if total_est > 0 else 0


        resumen.append({
            'usuario': estudiante['usuario'],
            'grupo': estudiante.get('grupo', 'Sin grupo'),
            'asistio': asistio_est,
            'falto': falto_est,
            'porcentaje': porcentaje_est
        })

    return render_template(
        'estadisticas.html',
        total = total,
        asistieron = asistieron,
        faltaron = faltaron,
        porcentaje = porcentaje_asistencia,
        resumen=resumen
    )

@app.route('/mis_estadisticas')
def mis_estadisticas():

    usuario = session['usuario']

    total = asistencias_collection.count_documents({
        'usuario': usuario
    })

    asistio = asistencias_collection.count_documents({
        'usuario': usuario,
        'estado': 'si'
    })

    faltas = asistencias_collection.count_documents({
        'usuario': usuario,
        'estado': 'no'
    })

    porcentaje = round(
        (asistio / total) * 100,
        2
    ) if total > 0 else 0

    return render_template(
        'mis_estadisticas.html',
        total=total,
        asistio=asistio,
        faltas=faltas,
        porcentaje=porcentaje
    )

@app.route('/mi_perfil')
def mi_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    user_data = collection.find_one({'usuario': usuario})
    return render_template('mi_perfil.html', usuario=user_data['usuario'], email=user_data['email'], direccion=user_data.get('direccion', 'No registrada'), rol=user_data['rol'])

@app.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        usuario = collection.find_one({'email': email})

        if usuario:
            token = serializer.dumps(email, salt='password-reset-salt')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            asunto = "Recuperación de contraseña"
            cuerpo = f"""
            <p>Hola, hemos recibido una solicitud para restablecer tu contraseña.</p>
            <p>Si no has solicitado este cambio, ignora este mensaje.</p>
            <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
            <a href="{enlace}">Restablecer contraseña</a>
            """
            enviar_email(email, asunto, cuerpo)
            flash("Te hemos enviado un correo para recuperar tu contraseña.", "success")
        else:
            flash("El correo electrónico no está registrado.", "error")

    return render_template('recuperar_contrasena.html')

@app.route('/restablecer_contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash("El enlace de restablecimiento ha caducado o es inválido.", "error")
        return redirect(url_for('recuperar_contrasena'))

    if request.method == 'POST':
        nueva_contrasena = request.form['nueva_contrasena']
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        collection.update_one({'email': email}, {'$set': {'contrasena': hashed_password}})
        flash("Tu contraseña ha sido restablecida con éxito.", "success")
        return redirect(url_for('login'))

    return render_template('restablecer_contrasena.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario_actual = session['usuario']

    user_data = collection.find_one({
        'usuario': usuario_actual
    })

    if request.method == 'POST':

        nuevo_usuario = request.form['usuario']
        nuevo_email = request.form['email']
        nueva_direccion = request.form['direccion']

        collection.update_one(
            {'usuario': usuario_actual},
            {
                '$set': {
                    'usuario': nuevo_usuario,
                    'email': nuevo_email,
                    'direccion': nueva_direccion
                }
            }
        )

        session['usuario'] = nuevo_usuario

        flash("Perfil actualizado correctamente")

        return redirect(url_for('mi_perfil'))

    return render_template(
        'editar_perfil.html',
        usuario=user_data['usuario'],
        email=user_data['email'],
        direccion=user_data.get('direccion', '')
    )

@app.route('/tareas', methods=['GET', 'POST'])
def tareas():

    if request.method == 'POST':

        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        grupo = request.form['grupo']
        fecha_entrega = request.form['fecha_entrega']

        tareas_collction.insert_one({
            'titulo': titulo,
            'descripcion': descripcion,
            'grupo': grupo,
            'fecha_entrega': fecha_entrega
        })

        flash('Tarea creada correctamente')

        return redirect(url_for('tareas'))
    
    lista_tareas = tareas_collction.find()

    return render_template ('tareas.html', tareas=lista_tareas)

@app.route('/eliminar_tarea/<id>')
def eliminar_tarea(id):

    tareas_collction.delete_one({
        '_id': ObjectId(id)
    })

    flash("Tareas eliminada correctamente")

    return redirect(url_for('tareas'))

@app.route('/editar_tarea/<id>', methods=['GET', 'POST'])
def editar_tarea(id):

    tarea = tareas_collction.find_one({
        '_id': ObjectId(id)
    })

    if request.method == 'POST':

        tareas_collction.update_one(
            {'_id': ObjectId(id)},
            {
                '$set':{
                    'titulo': request.form['titulo'],
                    'descripcion': request.form['descripcion'],
                    'grupo': request.form['grupo']
                }
            }
        )

        flash("Tarea actualizada correctamente")

        return redirect(url_for('tareas'))

    lista_tareas = tareas_collction.find()

    return render_template(
        'tareas.html',
        tarea=tarea,
        tareas=lista_tareas
    )

@app.route('/mis_tareas')
def mis_tareas():

    usuario = session['usuario']

    estudiante = collection.find_one({
        'usuario': usuario
    })

    grupo = estudiante.get('grupo', '')

    tareas = list(
        tareas_collction.find({
            'grupo': grupo
        })
    )

    for tarea in tareas:

        entrega = entregas_collction.find_one({
            'tarea_id': str(tarea['_id']),
            'usuario': usuario
        })

        if entrega:
            tarea['nota'] = entrega.get('nota', '')
            tarea['comentario'] = entrega.get('comentario', '')
            tarea['estado'] = entrega.get('estado', '')
        else:
            tarea['nota'] = ''
            tarea['comentario'] = ''
            tarea['estado'] = 'Pendiente'

    return render_template(
        'mis_tareas.html',
        tareas=tareas
    )

@app.route('/entregar_tarea', methods=['POST'])
def entregar_tarea():

    archivo = request.files['archivo']

    tarea_id = request.form['tarea_id']

    usuario = session['usuario']

    if archivo:

        nombre_archivo = secure_filename(
            archivo.filename
        )

        archivo.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                nombre_archivo
            )
        )

        entregas_collction.insert_one({
            'tarea_id': tarea_id,
            'usuario': usuario,
            'archivo': nombre_archivo,
            'comentario': '',
            'nota':'',
            'estado': 'Entregado'
        })

        flash("Tarea entregada correctamente")

    return redirect(url_for('mis_tareas'))

@app.route('/entregas')
def entregas():

    entregas = list(entregas_collction.find())

    for entrega in entregas:

        usuario = collection.find_one({
            'usuario': entrega['usuario']
        })

        tarea = tareas_collction.find_one({
            '_id': ObjectId(entrega['tarea_id'])
        })

        entrega['grupo'] = usuario.get('grupo', '')
        entrega['titulo'] = tarea.get('titulo', '')

    return render_template(
        'entregas.html',
        entregas=entregas
    )
    
@app.route('/calificar/<id>', methods=['POST'])
def calificar(id):

    nota = request.form['nota']
    comentario = request.form['comentario']

    entregas_collction.update_one(
        {
            '_id': ObjectId(id)
        },
        {
            '$set': {
                'nota': nota,
                'comentario': comentario
            }
        }
    )

    flash("Calificación guardada")

    return redirect(url_for('entregas'))

from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from itsdangerous import URLSafeTimedSerializer as Serializer
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Clave secreta para sesiones
app.secret_key = "advpjsh"

UPLOAD_FOLDER = 'uploads'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configuración de MongoDB Atlas
client = MongoClient("mongodb+srv://vale:vale2026Mongo@usuarios.1ncbu1v.mongodb.net/?appName=Usuarios")
db = client['db1'] #Nombre de tu base de datos aquí
collection = db['usuarios'] #Nombre de tu colección aquí
asistencias_collection = db['asistencias']
tareas_collction = db['tareas']
entregas_collction = db['entregas']

# Configuración de SendGrid
SENDGRID_API_KEY = '' 

# Serializador para crear y verificar tokens
serializer = Serializer(app.secret_key, salt='password-reset-salt')

# Función para enviar correos
def enviar_email(destinatario, asunto, cuerpo):
    mensaje = Mail(
        from_email='valeria9griffith@gmail.com',  # Cambia esto por tu correo
        to_emails=destinatario,
        subject=asunto,
        html_content=cuerpo
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)  # Usa tu clave API de SendGrid directamente
        response = sg.send(mensaje)
        print(f"Correo enviado con éxito! Status code: {response.status_code}")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

@app.route('/')
def home():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('pagina_principal'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']
        contrasena = request.form['contrasena']
        direccion = request.form['direccion']
        rol = request.form['rol']
        grupo = request.form.get('grupo', '')

        # Verificar si el correo ya está registrado
        if collection.find_one({'email': email}):
            flash("El correo electrónico ya está registrado.")
            return redirect(url_for('registro'))

        # Hashear la contraseña
        hashed_password = bcrypt.generate_password_hash(contrasena).decode('utf-8')

        # Insertar usuario en la base de datos
        collection.insert_one({
            'usuario': usuario,
            'email': email,
            'contrasena': hashed_password,
            'direccion' : direccion,
            'rol': rol,
            'grupo': grupo
        })
        
        session['usuario'] = usuario
        session['rol'] = rol
        return redirect(url_for('pagina_principal'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        rol = request.form['rol']

        # Buscar al usuario en la base de datos
        user = collection.find_one({'usuario': usuario})
        
        # Verificar si las credenciales son correctas
        if user and bcrypt.check_password_hash(user['contrasena'], contrasena):

            if user['rol'] != rol:
                flash(f"Esta cuenta pertenece a un {user['rol']}.")
                return render_template('login.html')
            
            session['usuario'] = usuario
            session['rol'] = rol
            return redirect(url_for('pagina_principal'))
        else:
            flash("Usuario o contraseña incorrectos.")
            return render_template('login.html')

    return render_template('login.html')

@app.route('/pagina_principal')
def pagina_principal():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if session['rol'] == 'profesor':
        return render_template(
            'inicio_profesor.html',
            usuario=session['usuario']
        )
    return render_template(
        'inicio_estudiante.html',
        usuario=session['usuario']
    )

@app.route('/asistencias', methods=['GET', 'POST'])
def asistencias():

    if request.method == 'POST':

        grupo = request.form['grupo']
        fecha = request.form['fecha']

        estudiantes = collection.find({
            'rol': 'estudiante',
            'grupo': grupo
        })

        for estudiante in estudiantes:

            estado = request.form.get(
                f"asistencia_{estudiante['usuario']}"
            )

            asistencias_collection.insert_one({
                'usuario': estudiante['usuario'],
                'correo': estudiante['email'],
                'grupo': grupo,
                'fecha': fecha,
                'estado': estado
            })

        flash("Asistencias guardadas correctamente")

        return redirect(
            url_for(
                'asistencias',
                grupo=grupo,
                fecha=fecha
            )
        )

    grupo = request.args.get('grupo')
    fecha = request.args.get('fecha')

    estudiantes = []

    if grupo:
        estudiantes = collection.find({
            'rol': 'estudiante',
            'grupo': grupo
        })

    return render_template(
        'asistencias.html',
        estudiantes=estudiantes,
        grupo=grupo,
        fecha=fecha
    )

@app.route('/historial')
def historial():

    fecha = request.args.get('fecha')

    if fecha:
        historial = asistencias_collection.find({
            'fecha': fecha
        })

    else:
        historial = asistencias_collection.find()

    grupo1001 = asistencias_collection.find({'grupo': '1001'})
    grupo1002 = asistencias_collection.find({'grupo': '1002'})
    grupo1003 = asistencias_collection.find({'grupo': '1003'})
    grupo1004 = asistencias_collection.find({'grupo': '1004'})

    grupo1101 = asistencias_collection.find({'grupo': '1101'})
    grupo1102 = asistencias_collection.find({'grupo': '1102'})
    grupo1103 = asistencias_collection.find({'grupo': '1103'})
    grupo1104 = asistencias_collection.find({'grupo': '1104'})

    return render_template(
        'historial.html',
        grupo1001=grupo1001,
        grupo1002=grupo1002,
        grupo1003=grupo1003,
        grupo1004=grupo1004,
        grupo1101=grupo1101,
        grupo1102=grupo1102,
        grupo1103=grupo1103,
        grupo1104=grupo1104,
        historial=historial
    )
    
@app.route('/eliminar_asistencia/<id>')
def eliminar_asistencia(id):
     asistencias_collection.delete_one({
         '_id': ObjectId(id)
     })

     flash("Asistencia eliminada correctamente")

     return redirect(url_for('historial'))

@app.route('/editar_asistencia/<id>', methods=['GET', 'POST'])
def editar_asistencia(id):

    asistencia = asistencias_collection.find_one({
        '_id': ObjectId(id)
    })

    if request.method == 'POST':

        nuevo_estado = request.form['estado']

        asistencias_collection.update_one(
            {'_id': ObjectId(id)},
            {
                '$set':{
                    'estado': nuevo_estado
                }
            }
        )

        flash("Asistencia actualizada")

        return redirect(url_for('historial'))
    return render_template(
        'editar_asistencia.html',
        asistencia=asistencia
    )

@app.route('/estadisticas')
def estadisticas():

    total = asistencias_collection.count_documents({})

    asistieron = asistencias_collection.count_documents({
        'estado': 'si'
    })

    faltaron = asistencias_collection.count_documents({
        'estado': 'no'
    })

    porcentaje_asistencia = round(
        (asistieron / total) * 100,
        2
    ) if total > 0 else 0

    estudiantes = collection.find({
        'rol': 'estudiante'
    })

    resumen = []

    for estudiante in estudiantes:

        total_est = asistencias_collection.count_documents({
            'usuario' : estudiante['usuario']
        })

        asistio_est = asistencias_collection.count_documents({
            'usuario': estudiante['usuario'],
            'estado':'si'
        })

        falto_est = asistencias_collection.count_documents({
            'usuario': estudiante['usuario'],
            'estado': 'no'
        })

        porcentaje_est = round(
            (asistio_est / total_est) * 100,
            2
        ) if total_est > 0 else 0


        resumen.append({
            'usuario': estudiante['usuario'],
            'grupo': estudiante.get('grupo', 'Sin grupo'),
            'asistio': asistio_est,
            'falto': falto_est,
            'porcentaje': porcentaje_est
        })

    return render_template(
        'estadisticas.html',
        total = total,
        asistieron = asistieron,
        faltaron = faltaron,
        porcentaje = porcentaje_asistencia,
        resumen=resumen
    )

@app.route('/mis_estadisticas')
def mis_estadisticas():

    usuario = session['usuario']

    total = asistencias_collection.count_documents({
        'usuario': usuario
    })

    asistio = asistencias_collection.count_documents({
        'usuario': usuario,
        'estado': 'si'
    })

    faltas = asistencias_collection.count_documents({
        'usuario': usuario,
        'estado': 'no'
    })

    porcentaje = round(
        (asistio / total) * 100,
        2
    ) if total > 0 else 0

    return render_template(
        'mis_estadisticas.html',
        total=total,
        asistio=asistio,
        faltas=faltas,
        porcentaje=porcentaje
    )

@app.route('/mi_perfil')
def mi_perfil():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    user_data = collection.find_one({'usuario': usuario})
    return render_template('mi_perfil.html', usuario=user_data['usuario'], email=user_data['email'], direccion=user_data.get('direccion', 'No registrada'), rol=user_data['rol'])

@app.route('/recuperar_contrasena', methods=['GET', 'POST'])
def recuperar_contrasena():
    if request.method == 'POST':
        email = request.form['email']
        usuario = collection.find_one({'email': email})

        if usuario:
            token = serializer.dumps(email, salt='password-reset-salt')
            enlace = url_for('restablecer_contrasena', token=token, _external=True)
            asunto = "Recuperación de contraseña"
            cuerpo = f"""
            <p>Hola, hemos recibido una solicitud para restablecer tu contraseña.</p>
            <p>Si no has solicitado este cambio, ignora este mensaje.</p>
            <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
            <a href="{enlace}">Restablecer contraseña</a>
            """
            enviar_email(email, asunto, cuerpo)
            flash("Te hemos enviado un correo para recuperar tu contraseña.", "success")
        else:
            flash("El correo electrónico no está registrado.", "error")

    return render_template('recuperar_contrasena.html')

@app.route('/restablecer_contrasena/<token>', methods=['GET', 'POST'])
def restablecer_contrasena(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash("El enlace de restablecimiento ha caducado o es inválido.", "error")
        return redirect(url_for('recuperar_contrasena'))

    if request.method == 'POST':
        nueva_contrasena = request.form['nueva_contrasena']
        hashed_password = bcrypt.generate_password_hash(nueva_contrasena).decode('utf-8')
        collection.update_one({'email': email}, {'$set': {'contrasena': hashed_password}})
        flash("Tu contraseña ha sido restablecida con éxito.", "success")
        return redirect(url_for('login'))

    return render_template('restablecer_contrasena.html')

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/editar_perfil', methods=['GET', 'POST'])
def editar_perfil():

    if 'usuario' not in session:
        return redirect(url_for('login'))

    usuario_actual = session['usuario']

    user_data = collection.find_one({
        'usuario': usuario_actual
    })

    if request.method == 'POST':

        nuevo_usuario = request.form['usuario']
        nuevo_email = request.form['email']
        nueva_direccion = request.form['direccion']

        collection.update_one(
            {'usuario': usuario_actual},
            {
                '$set': {
                    'usuario': nuevo_usuario,
                    'email': nuevo_email,
                    'direccion': nueva_direccion
                }
            }
        )

        session['usuario'] = nuevo_usuario

        flash("Perfil actualizado correctamente")

        return redirect(url_for('mi_perfil'))

    return render_template(
        'editar_perfil.html',
        usuario=user_data['usuario'],
        email=user_data['email'],
        direccion=user_data.get('direccion', '')
    )

@app.route('/tareas', methods=['GET', 'POST'])
def tareas():

    if request.method == 'POST':

        titulo = request.form['titulo']
        descripcion = request.form['descripcion']
        grupo = request.form['grupo']
        fecha_entrega = request.form['fecha_entrega']

        tareas_collction.insert_one({
            'titulo': titulo,
            'descripcion': descripcion,
            'grupo': grupo,
            'fecha_entrega': fecha_entrega
        })

        flash('Tarea creada correctamente')

        return redirect(url_for('tareas'))
    
    lista_tareas = tareas_collction.find()

    return render_template ('tareas.html', tareas=lista_tareas)

@app.route('/eliminar_tarea/<id>')
def eliminar_tarea(id):

    tareas_collction.delete_one({
        '_id': ObjectId(id)
    })

    flash("Tareas eliminada correctamente")

    return redirect(url_for('tareas'))

@app.route('/editar_tarea/<id>', methods=['GET', 'POST'])
def editar_tarea(id):

    tarea = tareas_collction.find_one({
        '_id': ObjectId(id)
    })

    if request.method == 'POST':

        tareas_collction.update_one(
            {'_id': ObjectId(id)},
            {
                '$set':{
                    'titulo': request.form['titulo'],
                    'descripcion': request.form['descripcion'],
                    'grupo': request.form['grupo']
                }
            }
        )

        flash("Tarea actualizada correctamente")

        return redirect(url_for('tareas'))

    lista_tareas = tareas_collction.find()

    return render_template(
        'tareas.html',
        tarea=tarea,
        tareas=lista_tareas
    )

@app.route('/mis_tareas')
def mis_tareas():

    usuario = session['usuario']

    estudiante = collection.find_one({
        'usuario': usuario
    })

    grupo = estudiante.get('grupo', '')

    tareas = list(
        tareas_collction.find({
            'grupo': grupo
        })
    )

    for tarea in tareas:

        entrega = entregas_collction.find_one({
            'tarea_id': str(tarea['_id']),
            'usuario': usuario
        })

        if entrega:
            tarea['nota'] = entrega.get('nota', '')
            tarea['comentario'] = entrega.get('comentario', '')
            tarea['estado'] = entrega.get('estado', '')
        else:
            tarea['nota'] = ''
            tarea['comentario'] = ''
            tarea['estado'] = 'Pendiente'

    return render_template(
        'mis_tareas.html',
        tareas=tareas
    )

@app.route('/entregar_tarea', methods=['POST'])
def entregar_tarea():

    archivo = request.files['archivo']

    tarea_id = request.form['tarea_id']

    usuario = session['usuario']

    if archivo:

        nombre_archivo = secure_filename(
            archivo.filename
        )

        archivo.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                nombre_archivo
            )
        )

        entregas_collction.insert_one({
            'tarea_id': tarea_id,
            'usuario': usuario,
            'archivo': nombre_archivo,
            'comentario': '',
            'nota':'',
            'estado': 'Entregado'
        })

        flash("Tarea entregada correctamente")

    return redirect(url_for('mis_tareas'))

@app.route('/entregas')
def entregas():

    entregas = list(entregas_collction.find())

    for entrega in entregas:

        usuario = collection.find_one({
            'usuario': entrega['usuario']
        })

        tarea = tareas_collction.find_one({
            '_id': ObjectId(entrega['tarea_id'])
        })

        entrega['grupo'] = usuario.get('grupo', '')
        entrega['titulo'] = tarea.get('titulo', '')

    return render_template(
        'entregas.html',
        entregas=entregas
    )
    
@app.route('/calificar/<id>', methods=['POST'])
def calificar(id):

    nota = request.form['nota']
    comentario = request.form['comentario']

    entregas_collction.update_one(
        {
            '_id': ObjectId(id)
        },
        {
            '$set': {
                'nota': nota,
                'comentario': comentario
            }
        }
    )

    flash("Calificación guardada")

    return redirect(url_for('entregas'))

@app.route('/mis_notas')
def mis_notas():

    usuario = session['usuario']

    notas = list(
        entregas_collction.find({
            'usuario': usuario
        })
    )

    for nota in notas:

        tarea = tareas_collction.find_one({
            '_id': ObjectId(nota['tarea_id'])
        })

        if tarea:
            nota['titulo'] = tarea.get('titulo', '')

    return render_template(
        'mis_notas.html',
        notas=notas
    )

if __name__ == '__main__':
    app.run(debug=True) 

if __name__ == '__main__':
    app.run(debug=True) 