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
            query = "INSERT INTO tracks (track) VALUES (%s) RETURNING idtrack;"
            cur.execute(query, [track.track])  

            new_id = cur.fetchone()[0]
            conexion.commit()

        track.idtrack = new_id
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
            query = "SELECT track FROM tracks WHERE idtrack = %s"
            cur.execute(query, [track_id])
            row = cur.fetchone()
        if not row:
            return Error(code="404", message="Track not found"), 404

        return row[0]

    except Exception as e:
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
            query = "UPDATE tracks SET track = %s WHERE idtrack = %s;"
            cur.execute(query, [track.track, track_id])

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
            query = "DELETE FROM tracks WHERE idtrack = %s;"
            cur.execute(query, [track_id])
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