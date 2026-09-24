import grpc
from concurrent import futures

# Import des classes générées à l'étape précédente
from generated import user_pb2, user_pb2_grpc

# ---- 1. La base de données factice (simulée pour le cours) ----
FAKE_DB = {
    1: user_pb2.User(id=1, name="Mounir", email="mounir@example.com"),
    2: user_pb2.User(id=2, name="Alice", email="alice@example.com"),
}

# ---- 2. Le servicer : on hérite de la classe générée par protoc ----
class UserService(user_pb2_grpc.UserServiceServicer):
    """Chaque méthode du fichier .proto apparaît ici et doit être implémentée."""

    def GetUser(self, request, context):
        # request.user_id : le champ du message GetUserRequest, déjà décodé
        user = FAKE_DB.get(request.user_id)
        if user is None:
            # context permet d'envoyer une erreur gRPC standardisée au client
            context.abort(grpc.StatusCode.NOT_FOUND, f"User {request.user_id} introuvable")
        # On renvoie la réponse attendue par le contrat
        return user_pb2.GetUserResponse(user=user)

# ---- 3. Le serveur gRPC lui-même ----
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # On "enregistre" notre servicer auprès du serveur gRPC
    user_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    # Écoute sur le port 50051 (port conventionnel gRPC)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("✅ Serveur gRPC en écoute sur le port 50051")
    server.wait_for_termination()   # Bloque ici tant que le serveur tourne

if __name__ == "__main__":
    serve()
