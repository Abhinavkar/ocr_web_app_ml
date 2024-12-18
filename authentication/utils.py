# from pymongo import MongoClient
# from django.conf import settings

# def mongo_db_connection_establish():
#     try:
#         client = MongoClient(settings.MONGO_DB_URL)
#         print("Connected to MongoDB")
#         db = client.ocr_db
#         coll = db.auth_user

#         return client
#     except Exception as e:
#         print("Error in MongoDB Connection")
#         print(e)
#         return None
# def mongo_db_connection_close(client):
#     try:
#         client.close()
#         print("Connection Closed")
#     except Exception as e:
#         print("Error in Closing Connection")
#         print(e)
#         return None

# def insert_admin_user_data(client, data):
#     try:
#         db = client.ocr_db
#         coll = db.auth_user
#         coll.insert_one(data)
#         print("Data Inserted")
#     except Exception as e:
#         print("Error in Inserting Data")
#         print(e)
#         return None

# def get_user_data(client, data):
#     try:
#         db = client.ocr_db
#         coll = db.auth_user
#         data = coll.find_one(data)
#         print("Data Fetched")
#         return data
#     except Exception as e:
#         print("Error in Fetching Data")
#         print(e)
#         return None