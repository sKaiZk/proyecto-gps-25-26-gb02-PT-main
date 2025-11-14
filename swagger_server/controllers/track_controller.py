import connexion
import base64
import six
import io

from flask import send_file
from swagger_server.models.error import Error  # noqa: E501
from swagger_server.models.track import Track  # noqa: E501
from swagger_server import util
from swagger_server.controllers.dbconx.tempName import dbConectar, dbDesconectar
from swagger_server.controllers.authorization_controller import is_valid_token
import psycopg2 as DB


def check_auth(required_scopes=None):
    """
    Verifica autenticación defensiva (backup de Connexion).
    Devuelve (authorized, error_response) tuple.
    """
    token = connexion.request.cookies.get('oversound_auth')
    if not token or not is_valid_token(token):
        error = Error(code="401", message="Unauthorized: Missing or invalid token")
        return False, (error, 401)
    return True, None

def add_track(body):
    """Add a new track to the database"""
    # Verificar autenticación defensiva
    authorized, error_response = check_auth(required_scopes=['write:tracks'])
    if not authorized:
        return error_response
    
    if not connexion.request.is_json:
        return Error(code="400", message="Invalid JSON"), 400

    track = Track.from_dict(connexion.request.get_json())
    conexion = None

    try:
        conexion = dbConectar()
        if not conexion:
            return Error(code="500", message="Database connection failed"), 500

        with conexion.cursor() as cur:
            cur.execute("""
                INSERT INTO tracks (binary)
                VALUES (%s)
                RETURNING id;
            """, (track.binary,))  

            new_id = cur.fetchone()[0]
            conexion.commit()

        track.id = new_id
        return track, 201

    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error al crear track: {e}")
        return Error(code="500", message="Database error"), 500

    finally:
        if conexion:
            dbDesconectar(conexion)


def get_track(track_id):
    """Gets a track file directly (returns audio instead of base64 JSON)"""
    # Verificar autenticación defensiva
    authorized, error_response = check_auth(required_scopes=['read:tracks'])
    if not authorized:
        return error_response
    
    conexion = None
    try:
        conexion = dbConectar()
        if not conexion:
            return Error(code="500", message="Database connection failed"), 500

        with conexion.cursor() as cur:
            cur.execute("SELECT binary FROM tracks WHERE id = %s;", (track_id,))
            row = cur.fetchone()

        if not row:
            return Error(code="404", message="Track not found"), 404

        audio_bytes = row[0]  # PostgreSQL bytea → bytes en Python

        # Retornar el binario directamente como archivo de audio
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype="audio/mpeg",          # o "audio/wav" según tu formato real
            as_attachment=False,            # True si quieres que se descargue
            download_name=f"track_{track_id}.mp3"
        )

    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error al obtener track: {e}")
        return Error(code="500", message="Database error"), 500

    finally:
        if conexion:
            dbDesconectar(conexion)


def update_track(body, track_id):
    """Updates a track in the database"""
    # Verificar autenticación defensiva
    authorized, error_response = check_auth(required_scopes=['write:tracks'])
    if not authorized:
        return error_response
    
    if not connexion.request.is_json:
        return Error(code="400", message="Invalid JSON"), 400

    track = Track.from_dict(connexion.request.get_json())
    conexion = None

    try:
        conexion = dbConectar()
        if not conexion:
            return Error(code="500", message="Database connection failed"), 500

        with conexion.cursor() as cur:
            cur.execute("""
                UPDATE tracks
                SET binary = %s
                WHERE id = %s;
            """, (track.binary, track_id))

            if cur.rowcount == 0:
                conexion.rollback()
                return Error(code="404", message="Track not found"), 404

            conexion.commit()

        return '', 204

    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error al actualizar track: {e}")
        return Error(code="500", message="Database error"), 500

    finally:
        if conexion:
            dbDesconectar(conexion)


def delete_track(track_id):
    """Deletes a track"""
    # Verificar autenticación defensiva
    authorized, error_response = check_auth(required_scopes=['write:tracks'])
    if not authorized:
        return error_response
    
    conexion = None
    try:
        conexion = dbConectar()
        if not conexion:
            return Error(code="500", message="Database connection failed"), 500

        with conexion.cursor() as cur:
            cur.execute("DELETE FROM tracks WHERE id = %s;", (track_id,))
            if cur.rowcount == 0:
                conexion.rollback()
                return Error(code="404", message="Track not found"), 404

            conexion.commit()

        return '', 204

    except Exception as e:
        if conexion:
            conexion.rollback()
        print(f"Error al eliminar track: {e}")
        return Error(code="500", message="Database error"), 500

    finally:
        if conexion:
            dbDesconectar(conexion)