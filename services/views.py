
from bson import ObjectId
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from authentication.db_wrapper import get_collection
from authentication.permissions import IsAdmin, IsSubAdmin,IsSuperStaff,IsUser
from bson.objectid import ObjectId

class Organization_View(APIView):

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsSuperStaff()]  
        elif self.request.method == 'DELETE':
            return [IsSuperStaff()]  
        elif self.request.method == 'PUT':
            return [IsSuperStaff()] 
        return super().get_permissions()
    
    def get(self, request):
        organization_collection = get_collection('organization_db')
        organization = list(organization_collection.find())
        for org in organization:
            org["_id"] = str(org["_id"])  
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

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsSuperStaff() and IsAdmin()]  
        elif self.request.method == 'DELETE':
            return [IsSuperStaff() and IsAdmin()]  
        elif self.request.method == 'PUT':
            return [IsSuperStaff() and IsAdmin()] 
        return super().get_permissions()

    def get(self, request, id=None):
        
        classes_collection = get_collection("classes")
        if id:
            classes = list(classes_collection.find({"organization_id": id}))
        else :
            return Response({"message":"Internal Server Error "}, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        for cls in classes:
            cls["_id"] = str(cls["_id"])  # Convert ObjectId to string
        return Response(classes, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        
        if not data.get("name") or not data.get("organization_id"):
            return Response({"message": "Please provide both class name and organization ID"}, status=status.HTTP_400_BAD_REQUEST)

        data["organization_id"] = data.get("organization_id")
        
        classes_collection = get_collection("classes")
        
        if classes_collection.find_one({"name": data["name"], "organization_id": data["organization_id"]}):
            return Response({"error": "Class already exists for this organization"}, status=400)
        
        classes_collection.insert_one(data)
        return Response({"message": "Class created successfully"}, status=status.HTTP_201_CREATED)
    
    
    def delete(self, request, id):
        user_id=request.headers.get('userId')
        user_collection = get_collection('auth_users')
        classes_collection = get_collection("classes")
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        class_obj = classes_collection.find_one({"_id": ObjectId(id)})
        class_org = class_obj.get('organization_id')
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user_org_id = user.get('organization')
        print(user_org_id , class_org)
        if user_org_id != class_org:
            return Response({"error": "hii Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        result = classes_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return Response({"message": "Class not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Class deleted successfully"}, status=status.HTTP_200_OK)
    
    
    def put(self, request, id):
        user_id = request.headers.get('userId')
        user_collection = get_collection('auth_users')
        classes_collection = get_collection("classes")
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        class_obj = classes_collection.find_one({"_id": ObjectId(id)})
        class_org = class_obj.get('organization_id')
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user_org_id = user.get('organization')
        print(user_org_id, class_org)
        if user_org_id != class_org:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        new_class_name = request.data.get('name')
        if not new_class_name:
            return Response({"message": "Please provide the new class name"}, status=status.HTTP_400_BAD_REQUEST)
        
        result = classes_collection.update_one({"_id": ObjectId(id)}, {"$set": {"name": new_class_name}})
        if result.matched_count == 0:
            return Response({"message": "Class not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Class name updated successfully"}, status=status.HTTP_200_OK)

    
class SectionListCreateAPI(APIView):
    
    def get(self, request, class_id=None):
        if not class_id:
            return Response({"message": "Class ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        sections_collection = get_collection("sections")  # Assuming 'sections' is the collection name in MongoDB
        sections = list(sections_collection.find({"class_id": class_id}))

        if sections:
            for section in sections:
                section["_id"] = str(section["_id"])  # Convert ObjectId to string
            return Response(sections, status=status.HTTP_200_OK)
        
        return Response({"message": "No sections found for this class."}, status=status.HTTP_404_NOT_FOUND)
    def post(self, request):
        data = request.data
        if not data.get("name") or not data.get("class_id"):
            return Response({"message": "Please provide both section name and class ID"}, status=status.HTTP_400_BAD_REQUEST)

        sections_collection = get_collection("sections")
        if sections_collection.find_one({"name": data["name"], "class_id": data["class_id"]}):
            return Response({"error": "Section already exists for this class"}, status=status.HTTP_400_BAD_REQUEST)

        sections_collection.insert_one(data)
        return Response({"message": "Section created successfully"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        sections_collection = get_collection("sections")
        result = sections_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return Response({"message": "Section not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Section deleted successfully"}, status=status.HTTP_200_OK)

    def put(self, request, id):
        data = request.data
        if not data:
            return Response({"message": "Please provide the data to update"}, status=status.HTTP_400_BAD_REQUEST)
        sections_collection = get_collection("sections")
        result = sections_collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        if result.matched_count == 0:
            return Response({"message": "Section not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Section updated successfully"}, status=status.HTTP_200_OK)
    
    

class SubjectListCreateAPI(APIView):
    def get(self, request, section_id=None):
        subjects_collection = get_collection("subjects")

        # Build query dynamically based on provided section ID
        query = {}
        if section_id:
            query["associated_section_id"] = section_id

        subjects = list(subjects_collection.find(query))
        for subject in subjects:
            subject["_id"] = str(subject["_id"])  # Convert ObjectId to string

        return Response(subjects, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if not data.get("name") or not data.get("associated_section_id"):
            return Response(
                {"message": "Please provide subject name and associated section ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subjects_collection = get_collection("subjects")
        if subjects_collection.find_one({
            "name": data["name"],
            "associated_section_id": data["associated_section_id"],
        }):
            return Response({"error": "Subject already exists for this section"}, status=400)

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

class ClassListAll(APIView):
    def get(self, request, id=None):
        classes_collection = get_collection("classes")
        if id:
            classes = classes_collection.find_one({"_id": ObjectId(id)})
            if classes:
                classes["_id"] = str(classes["_id"])  # Convert ObjectId to string
                return Response(classes, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Class not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            classes = list(classes_collection.find())
            for cls in classes:
                cls["_id"] = str(cls["_id"])  # Convert ObjectId to string
            return Response(classes, status=status.HTTP_200_OK)

class DocumentListAPI(APIView):
    def get(self, request):
        try:
            # Fetch user ID from request header
            user_id = request.headers.get("userId")
            if not user_id:
                return Response(
                    {"message": "User ID is required in the request header"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            question_db_collection = get_collection('question_db')
            pdf_books_collection = get_collection('pdf_books')
            auth_users_collection = get_collection('auth_users')

            # Check if user exists
            user = auth_users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return Response(
                    {"message": "Invalid user ID or user not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            data = {}

            # Fetch class_selected, subject_selected, and question_file_path
            try:
                questions = question_db_collection.find({}, {
                    "class_selected": 1,
                    "subject_selected": 1,
                    "question_file_path": 1,
                })
                data["questions"] = [
                    {
                        "class_selected": question.get("class_selected"),
                        "subject_selected": question.get("subject_selected"),
                        "question_file_path": question.get("question_file_path"),
                    }
                    for question in questions
                ]
            except Exception as e:
                data["questions_error"] = str(e)

            # Fetch PDF book details
            try:
                pdf_books = pdf_books_collection.find({}, {
                    "subject": 1,
                    "section": 1,
                    "pdf_file_path": 1,
                })
                data["pdf_books"] = [
                    {
                        "section": pdf_book.get("section"),
                        "subject": pdf_book.get("subject"),
                        "pdf_file_path": pdf_book.get("pdf_file_path"),
                    }
                    for pdf_book in pdf_books
                ]
            except Exception as e:
                data["pdf_books_error"] = str(e)

            # Fetch user data
            try:
                users = auth_users_collection.find({}, {"_id": 1, "organization": 1})
                data["user_data"] = [
                    {
                        "user_id": str(user["_id"]),
                        "organization_id": str(user.get("organization", "N/A")),  # Handle missing organization_id
                    }
                    for user in users
                ]
            except Exception as e:
                data["user_data_error"] = str(e)

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": "An unexpected error occurred while fetching data", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
