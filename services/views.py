
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from authentication.db_wrapper import get_collection


class Organization_View(APIView):
    def get(self,request):
        organization_collection = get_collection('organization_db')
        organization = organization_collection.find()
        return Response(organization,status=200)
    
    def post(self,request):
        data = request.data
        organization_name = request.data.get('organization_name')
        if not all([organization_name]):
            return Response({"message": "Please provide all the details"}, status=status.HTTP_400_BAD_REQUEST)
        organization_collection = get_collection('organization_db')
        organization_collection.insert_one({'organization_name':organization_name})

        return Response({"message":f"{organization_name} added successfully"},status=201)
    def delete(self,request):
        organization_name = request.data.get('organization_name')
        organization_collection = get_collection('organization_db')
        organization_collection.delete_one({'organization_name':organization_name})
        return Response({"message":f"{organization_name} deleted successfully"},status=200)
    def put(self,request):
        old_organization_name = request.data.get('old_organization_name')
        new_organization_name = request.data.get('new_organization_name')
        organization_collection = get_collection('organization_db')
        organization_collection.update_one({'organization_name':old_organization_name},{'$set':{'organization_name':new_organization_name}})
        return Response({"message":f"{old_organization_name} updated to {new_organization_name}"},status=200)
    

class ClassListCreateAPI(APIView):

    def get(self, request):
        classes_collection = get_collection("classes")
        classes = list(classes_collection.find({}))
        for cls in classes:
            cls["_id"] = str(cls["_id"])  # Convert ObjectId to string
        return Response(classes, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        classes_collection = get_collection("classes")
        if classes_collection.find_one({"name": data["name"]}):
            return Response({"error": "Class already exists"}, status=400)
        classes_collection.insert_one(data)
        return Response({"message": "Class created successfully"}, status=status.HTTP_201_CREATED)
    def delete(self,request):
        return 
    def put(self,request):
        return
    


class SubjectListCreateAPI(APIView):
    
    def get(self, request, id=None):
        subjects_collection = get_collection("subjects")
        if id:
            subjects = list(subjects_collection.find({"associated_class_id": id}))
        else:
            subjects = list(subjects_collection.find({}))
        for subject in subjects:
            subject["_id"] = str(subject["_id"]) 
        return Response(subjects, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        subjects_collection = get_collection("subjects")
        if subjects_collection.find_one({"name": data["name"], "associated_class_id": data["associated_class_id"]}):
            return Response({"error": "Subject already exists for this class"}, status=400)
        subjects_collection.insert_one(data)
        return Response({"message": "Subject created successfully"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        
        subjects_collection = get_collection("subjects")
        subjects_collection.delete_one({"_id": ObjectId(id)})
        return Response({"message": "Subject deleted successfully"}, status=status.HTTP_200_OK)
    
    def put(self, request, id):
        data = request.data
        subjects_collection = get_collection("subjects")
        subjects_collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        return Response({"message": "Subject updated successfully"}, status=status.HTTP_200_OK)
    