
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from authentication.db_wrapper import get_collection


class Organization_View(APIView):
    def get(self, request):
        organization_collection = get_collection('organization_db')
        organization = list(organization_collection.find())
        for org in organization:
            org["_id"] = str(org["_id"])  # Convert ObjectId to string
        return Response(organization, status=200)
    
    def post(self, request):
        data = request.data
        organization_name = data.get('organization_name')
        if not organization_name:
            return Response({"message": "Please provide the organization name"}, status=status.HTTP_400_BAD_REQUEST)
        organization_collection = get_collection('organization_db')
        if organization_collection.find_one({'organization_name': organization_name}):
            return Response({"message": "Organization already exists"}, status=status.HTTP_400_BAD_REQUEST)
        organization_collection.insert_one({'organization_name': organization_name})
        return Response({"message": f"{organization_name} added successfully"}, status=201)
    
    def delete(self, request, id):
        organization_name = request.data.get('organization_name')
        if not organization_name:
            return Response({"message": "Please provide the organization name"}, status=status.HTTP_400_BAD_REQUEST)
        organization_collection = get_collection('organization_db')
        result = organization_collection.delete_one({'organization_name': organization_name})
        if result.deleted_count == 0:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"{organization_name} deleted successfully"}, status=200)
    
    def put(self, request, id):
        old_organization_name = request.data.get('old_organization_name')
        new_organization_name = request.data.get('new_organization_name')
        if not old_organization_name or not new_organization_name:
            return Response({"message": "Please provide both old and new organization names"}, status=status.HTTP_400_BAD_REQUEST)
        organization_collection = get_collection('organization_db')
        result = organization_collection.update_one({'organization_name': old_organization_name}, {'$set': {'organization_name': new_organization_name}})
        if result.matched_count == 0:
            return Response({"message": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": f"{old_organization_name} updated to {new_organization_name}"}, status=200)
    

class ClassListCreateAPI(APIView):

    def get(self, request, organization_id=None):
        classes_collection = get_collection("classes")
        if organization_id:
            classes = list(classes_collection.find({"organization_id": organization_id}))
        else:
            classes = list(classes_collection.find({}))
        
        for cls in classes:
            cls["_id"] = str(cls["_id"])  # Convert ObjectId to string
        return Response(classes, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if not data.get("name") or not data.get("organization_id"):
            return Response({"message": "Please provide the class name and organization ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        classes_collection = get_collection("classes")
        if classes_collection.find_one({"name": data["name"], "organization_id": data["organization_id"]}):
            return Response({"error": "Class already exists for this organization"}, status=400)
        
        classes_collection.insert_one(data)
        return Response({"message": "Class created successfully"}, status=status.HTTP_201_CREATED)
    
    
    def delete(self, request):
        return 
    
    def put(self, request):
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
        if not data.get("name") or not data.get("associated_class_id"):
            return Response({"message": "Please provide both subject name and associated class ID"}, status=status.HTTP_400_BAD_REQUEST)
        subjects_collection = get_collection("subjects")
        if subjects_collection.find_one({"name": data["name"], "associated_class_id": data["associated_class_id"]}):
            return Response({"error": "Subject already exists for this class"}, status=400)
        subjects_collection.insert_one(data)
        return Response({"message": "Subject created successfully"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        subjects_collection = get_collection("subjects")
        result = subjects_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return Response({"message": "Subject not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Subject deleted successfully"}, status=status.HTTP_200_OK)
    
    def put(self, request, id):
        data = request.data
        if not data:
            return Response({"message": "Please provide the data to update"}, status=status.HTTP_400_BAD_REQUEST)
        subjects_collection = get_collection("subjects")
        result = subjects_collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        if result.matched_count == 0:
            return Response({"message": "Subject not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Subject updated successfully"}, status=status.HTTP_200_OK)
    