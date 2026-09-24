import grpc

from protos import user_pb2, user_pb2_grpc


def fetch(stub, user_id):
    """Un appel RPC + la gestion d'erreur qui va avec."""
    try:
        # 3. L'appel RPC : comme une fonction locale... qui traverse le réseau
        response = stub.GetUser(user_pb2.GetUserRequest(user_id=user_id))
    except grpc.RpcError as err:
        # Un échec gRPC n'est PAS une exception métier Python : c'est un statut
        # transporté sur le réseau. L'objet err est aussi un grpc.Call, donc il
        # expose .code() (l'enum StatusCode) et .details() (le message serveur).
        print(f"❌ id={user_id} → {err.code().name} : {err.details()}")
        return

    user = response.user
    print(f"✅ id={user_id} → {user.name} ({user.nickname}) <{user.email}>")
    # HasField ne marche que sur les sous-messages : il distingue "absent" de
    # "présent mais vide". Sur un champ scalaire proto3 il lèverait ValueError.
    if user.HasField("address"):
        print(f"   adresse : {user.address.street}, {user.address.city}")
    else:
        print("   adresse : non renseignée")


# 1. Un "channel" = la connexion vers le serveur (comme une prise électrique)
with grpc.insecure_channel("localhost:50051") as channel:
    # 2. Le stub = le client généré qui connaît les méthodes du service
    stub = user_pb2_grpc.UserServiceStub(channel)

    fetch(stub, 1)    # cas nominal
    fetch(stub, 999)  # id inexistant → le serveur répond NOT_FOUND
