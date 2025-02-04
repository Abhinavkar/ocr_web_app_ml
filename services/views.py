
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
            return [ IsAdmin()]  
        elif self.request.method == 'DELETE':
            print("Checking permission")
            return [IsAdmin()]  
        elif self.request.method == 'PUT':
            return [IsAdmin()] 
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

        organization_id = data.get("organization_id")
        
        organizations_collection = get_collection("organization_db")
        organization = organizations_collection.find_one({"_id": ObjectId(organization_id)})
        if not organization:
            return Response({"message": "Invalid organization ID"}, status=status.HTTP_400_BAD_REQUEST)
        classes_collection = get_collection("classes")
        if classes_collection.find_one({"name": data["name"], "organization_id": organization_id}):
            return Response({"error": "Class already exists for this organization"}, status=status.HTTP_400_BAD_REQUEST)
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
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsSuperStaff() and IsAdmin()]  
        elif self.request.method == 'DELETE':
            return [IsSuperStaff() and IsAdmin()]  
        elif self.request.method == 'PUT':
            return [IsSuperStaff() and IsAdmin()] 
        return super().get_permissions()

    
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
        
        # Validate that both name, class_id, and organization_id are provided
        if not data.get("name") or not data.get("class_id") or not data.get("organization_id"):
            return Response({"message": "Please provide section name, class ID, and organization ID"}, status=status.HTTP_400_BAD_REQUEST)

        class_id = data.get("class_id")
        organization_id = data.get("organization_id")
        
        # Ensure organization_id is valid
        organizations_collection = get_collection("organization_db")
        organization = organizations_collection.find_one({"_id": ObjectId(organization_id)})
        if not organization:
            return Response({"message": "Invalid organization ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure class_id is valid and belongs to the organization
        classes_collection = get_collection("classes")
        class_obj = classes_collection.find_one({"_id": ObjectId(class_id), "organization_id": organization_id})
        if not class_obj:
            return Response({"message": "Invalid class ID or class does not belong to the organization"}, status=status.HTTP_400_BAD_REQUEST)
        
        sections_collection = get_collection("sections")
        
        # Check if the section already exists for the class
        if sections_collection.find_one({"name": data["name"], "class_id": class_id}):
            return Response({"error": "Section already exists for this class"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Insert the new section
        sections_collection.insert_one(data)
        return Response({"message": "Section created successfully"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user_id = request.headers.get('userId')
        user_collection = get_collection('auth_users')
        sections_collection = get_collection("sections")
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
        result = sections_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return Response({"message": "Section not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Section deleted successfully"}, status=status.HTTP_200_OK)

    def put(self, request, id):
        user_id = request.headers.get('userId')
        user_collection = get_collection('auth_users')
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not (user.get('is_admin') or user.get('is_sub_admin')):
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        if not data:
            return Response({"message": "Please provide the data to update"}, status=status.HTTP_400_BAD_REQUEST)
        
        sections_collection = get_collection("sections")
        result = sections_collection.update_one({"_id": ObjectId(id)}, {"$set": data})
        if result.matched_count == 0:
            return Response({"message": "Section not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Section updated successfully"}, status=status.HTTP_200_OK)
    

class OrgSectionListAPI(APIView):
    def get(self, request, organization_id=None):
        if not organization_id:
            return Response({"message": "Organization ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        sections_collection = get_collection("sections") 
        print(f"Fetching sections for organization_id: {organization_id}")
        sections = list(sections_collection.find({"organization_id": organization_id}))

        if sections:
            for section in sections:
                # Convert ObjectId to string
                section["_id"] = str(section["_id"])

                # Rename 'name' to 'section_name'
                if "name" in section:
                    section["section_name"] = section.pop("name")
            
            return Response(sections, status=status.HTTP_200_OK)
        
        return Response({"message": "No sections found for this organization."}, status=status.HTTP_404_NOT_FOUND)

    
class OrgSubjectListAPI(APIView):
    def get(self, request, organization_id=None):
        if not organization_id:
            return Response({"message": "Organization ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        subjects_collection = get_collection("subjects")
        print(f"Fetching subjects for organization_id: {organization_id}")
        subjects = list(subjects_collection.find({"organization_id": organization_id}))

        if subjects:
            for subject in subjects:
                subject["_id"] = str(subject["_id"])  # Convert ObjectId to string
                
                if "name" in subject:
                    subject["subject_name"] = subject.pop("name")
            return Response(subjects, status=status.HTTP_200_OK)
        
        return Response({"message": "No subjects found for this organization."}, status=status.HTTP_404_NOT_FOUND)
    
    
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
        
        if not data.get("name") or not data.get("associated_section_id") or not data.get("organization_id"):
            return Response(
                {"message": "Please provide subject name, associated section ID, and organization ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        associated_section_id = data.get("associated_section_id")
        organization_id = data.get("organization_id")
        
        # Ensure organization_id is valid
        organizations_collection = get_collection("organization_db")
        organization = organizations_collection.find_one({"_id": ObjectId(organization_id)})
        if not organization:
            return Response({"message": "Invalid organization ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure associated_section_id is valid and belongs to the organization
        sections_collection = get_collection("sections")
        section_obj = sections_collection.find_one({"_id": ObjectId(associated_section_id), "organization_id": organization_id})
        if not section_obj:
            return Response({"message": "Invalid section ID or section does not belong to the organization"}, status=status.HTTP_400_BAD_REQUEST)
        
        subjects_collection = get_collection("subjects")
        
        # Check if the subject already exists for the section
        if subjects_collection.find_one({"name": data["name"], "associated_section_id": associated_section_id}):
            return Response({"error": "Subject already exists for this section"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Insert the new subject
        subjects_collection.insert_one(data)
        return Response({"message": "Subject created successfully"}, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        user_id = request.headers.get('userId')
        user_collection = get_collection('auth_users')
        subjects_collection = get_collection("subjects")
        sections_collection = get_collection("sections")
        
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        subject_obj = subjects_collection.find_one({"_id": ObjectId(id)})
        if not subject_obj:
            return Response({"message": "Subject not found"}, status=status.HTTP_404_NOT_FOUND)
        
        section_obj = sections_collection.find_one({"_id": ObjectId(subject_obj.get('associated_section_id'))})
        if not section_obj:
            return Response({"message": "Section not found"}, status=status.HTTP_404_NOT_FOUND)
        
        section_org = section_obj.get('organization_id')
        user_org_id = user.get('organization')
    
        if user_org_id != section_org:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
        
        result = subjects_collection.delete_one({"_id": ObjectId(id)})
        if result.deleted_count == 0:
            return Response({"message": "Subject not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Subject deleted successfully"}, status=status.HTTP_200_OK)

    def put(self, request, id):
        user_id = request.headers.get('userId')
        user_collection = get_collection('auth_users')
        subjects_collection = get_collection("subjects")
        sections_collection = get_collection("sections")
    
        user = user_collection.find_one({"_id": ObjectId(user_id)})
    
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        subject_obj = subjects_collection.find_one({"_id": ObjectId(id)})
        if not subject_obj:
            return Response({"message": "Subject not found"}, status=status.HTTP_404_NOT_FOUND)
        
        section_obj = sections_collection.find_one({"_id": ObjectId(subject_obj.get('associated_section_id'))})
        if not section_obj:
            return Response({"message": "Section not found"}, status=status.HTTP_404_NOT_FOUND)
        
        section_org = section_obj.get('organization_id')
        user_org_id = user.get('organization')
      
        if user_org_id != section_org:
            return Response({"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

        new_name = request.data.get('name')
        if not new_name:
            return Response({"message": "Please provide the new name"}, status=status.HTTP_400_BAD_REQUEST)
        
        result = subjects_collection.update_one({"_id": ObjectId(id)}, {"$set": {"name": new_name}})
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
        
class SubjectGetById(APIView):
      def get(self, request, id=None):
        subject_collection = get_collection("subjects")
        if id:
            classes = subject_collection.find_one({"_id": ObjectId(id)})
            if classes:
                classes["_id"] = str(classes["_id"])  # Convert ObjectId to string
                return Response(classes, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Class not found"}, status=status.HTTP_404_NOT_FOUND)
        else:
            classes_collection = get_collection("classes")
            classes = list(classes_collection.find())
            for cls in classes:
                cls["_id"] = str(cls["_id"])  # Convert ObjectId to string
            return Response(classes, status=status.HTTP_200_OK)

# class DocumentListAPI(APIView):
#     def get(self, request):
#         try:
           
#             user_id = request.headers.get("userId")
#             if not user_id:
#                 return Response(
#                     {"message": "User ID is required in the request header"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             question_db_collection = get_collection('question_db')
#             pdf_books_collection = get_collection('pdf_books')
#             auth_users_collection = get_collection('auth_users')

            
#             user = auth_users_collection.find_one({"_id": ObjectId(user_id)})
#             if not user:
#                 return Response(
#                     {"message": "Invalid user ID or user not found"},
#                     status=status.HTTP_404_NOT_FOUND,
#                 )

#             data = {}

           
#             try:
#                 questions = question_db_collection.find({}, {
#                     "class_selected": 1,
#                     "subject_selected": 1,
#                     "question_file_path": 1,
#                 })
#                 data["questions"] = [
#                     {
#                         "class_selected": question.get("class_selected"),
#                         "subject_selected": question.get("subject_selected"),
#                         "question_file_path": question.get("question_file_path"),
#                     }
#                     for question in questions
#                 ]
#             except Exception as e:
#                 data["questions_error"] = str(e)

            
#             try:
#                 pdf_books = pdf_books_collection.find({}, {
#                     "subject": 1,
#                     "section": 1,
#                     "pdf_file_path": 1,
#                 })
#                 data["pdf_books"] = [
#                     {
#                         "section": pdf_book.get("section"),
#                         "subject": pdf_book.get("subject"),
#                         "pdf_file_path": pdf_book.get("pdf_file_path"),
#                     }
#                     for pdf_book in pdf_books
#                 ]
#             except Exception as e:
#                 data["pdf_books_error"] = str(e)

            
#             try:
#                 users = auth_users_collection.find({}, {"_id": 1, "organization": 1})
#                 data["user_data"] = [
#                     {
#                         "user_id": str(user["_id"]),
#                         "organization_id": str(user.get("organization", "N/A")),  # Handle missing organization_id
#                     }
#                     for user in users
#                 ]
#             except Exception as e:
#                 data["user_data_error"] = str(e)

#             return Response(data, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response(
#                 {"message": "An unexpected error occurred while fetching data", "error": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )
            
   
class ExamIdById(APIView):
    def get(self, request):
        # user_id = request.headers.get('userId')
        organization_id = request.headers.get('organizationId')
        class_id = request.headers.get('classId')
        section_id = request.headers.get('sectionId')
        subject_id = request.headers.get('subjectId')
        
        # if not user_id:
        #     return Response({"message": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not organization_id or not class_id or not section_id or not subject_id:
            return Response({"message": "Organization ID, Class ID, Section ID, and Subject ID are required."}, status=status.HTTP_400_BAD_REQUEST)
     
        try:
            exam_id_collection = get_collection("examId_db")

            cursor = exam_id_collection.find({
                "organization_id": organization_id, 
                "class_id": class_id,
                "section_id": section_id,
                "subject_id": subject_id
            })

            exam_ids = list(cursor)

            if not exam_ids:
                return Response({"message": "Exam IDs not found."}, status=status.HTTP_404_NOT_FOUND)

            exam_id_list = [str(exam["_id"]) for exam in exam_ids]

            return Response({"exam_ids": exam_id_list}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
                
class DetailsAllAPI(APIView):
    def get(self, request):
        organization_id = request.headers.get('organizationId')

        if not organization_id:
            return Response({"message": "Organization ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            organization_collection = get_collection("organization_db")
            organization = organization_collection.find_one({"_id": ObjectId(organization_id)})
            if not organization:
                return Response({"message": "Organization not found."}, status=status.HTTP_404_NOT_FOUND)
            organization_name = organization.get('organization_name')

            classes_collection = get_collection("classes")
            classes = list(classes_collection.find({"organization_id": organization_id}))
            class_names = [cls.get('name') for cls in classes]
            class_count = len(classes)

            sections_collection = get_collection("sections")
            sections = list(sections_collection.find({"organization_id": organization_id}))
            section_names = [section.get('name') for section in sections]
            section_count = len(sections)

            subjects_collection = get_collection("subjects")
            subjects = list(subjects_collection.find({"organization_id": organization_id}))
            subject_names = [subject.get('name') for subject in subjects]
            subject_count = len(subjects)

            exam_id_collection = get_collection("examId_db")
            exam_ids = list(exam_id_collection.find({"organization_id": organization_id}))
            exam_id_list = [str(exam["_id"]) for exam in exam_ids]
            exam_count = len(exam_ids)
            active_count = sum(1 for exam in exam_ids if exam.get('is_active', False))
            inactive_count = exam_count - active_count

            user_collection = get_collection('auth_users')
            admin_count = user_collection.count_documents({"is_admin": True, "organization": organization_id})
            sub_admin_count = user_collection.count_documents({"is_sub_admin": True, "is_admin":False,  "organization": organization_id})
            super_staff_count = user_collection.count_documents({"is_super_staff": True, "organization": organization_id})
            user_count = user_collection.count_documents({
                "is_user": True,
                "is_super_staff": False,
                "is_admin": False,
                "is_sub_admin": False,
                "organization": organization_id
            })
            # total_user_count = user_collection.count_documents({"organization": organization_id})
            total_user_count = admin_count + sub_admin_count + super_staff_count + user_count

            admin_details = list(user_collection.find({"is_admin": True, "organization": organization_id}, {"_id": 0, "name": 1, "email": 1}))
            sub_admin_details = list(user_collection.find({"is_sub_admin": True, "organization": organization_id}, {"_id": 0, "name": 1, "email": 1}))
            super_staff_details = list(user_collection.find({"is_super_staff": True, "organization": organization_id}, {"_id": 0, "name": 1, "email": 1}))
            user_details = list(user_collection.find({"is_user": True, "organization": organization_id}, {"_id": 0, "name": 1, "email": 1}))

            return Response({
                "organization_name": organization_name,
                "class_names": class_names,
                "class_count": class_count,
                "section_names": section_names,
                "section_count": section_count,
                "subject_names": subject_names,
                "subject_count": subject_count,
                "exam_ids": exam_id_list,
                "exam_count": exam_count,
                "active_exam_count": active_count,
                "inactive_exam_count": inactive_count,
                "admin_count": admin_count,
                "sub_admin_count": sub_admin_count,
                "super_staff_count": super_staff_count,
                "user_count": user_count,
                "total_user_count": total_user_count,
                "department_count":"",
                "admin_details": admin_details,
                "sub_admin_details": sub_admin_details,
                "super_staff_details": super_staff_details,
                "user_details": user_details
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        

        
        
           
class GeneratedExamIdAPI(APIView):
    def get(self, request):
        user_id = request.headers.get('userId')
        
        if not user_id:
            return Response({"message": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user_collection = get_collection('auth_users')
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            exam_id_collection = get_collection("examId_db")
            exam_ids = list(exam_id_collection.find({"user_id": user_id}))

            for exam_id in exam_ids:
                exam_id["_id"] = str(exam_id["_id"])

            return Response({"exam_ids": exam_ids}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def put(self, request):
        user_id = request.headers.get('userId')
        exam_id = request.data.get('examId')
        is_active = request.data.get('is_active')
        
        if not user_id:
            return Response({"message": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not exam_id:
            return Response({"message": "Exam ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if is_active is None:
            return Response({"message": "is_active flag is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if isinstance(is_active, str):
            is_active = is_active.lower() == 'true'
        
        user_collection = get_collection('auth_users')
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            exam_id_collection = get_collection("examId_db")
            result = exam_id_collection.update_one(
                {"_id": exam_id, "user_id": user_id},
                {"$set": {"is_active": is_active}}
            )
            
            if result.matched_count == 0:
                return Response({"message": "Exam ID not found or not authorized to update."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response({"message": "Exam ID updated successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    def delete(self, request):
        user_id = request.headers.get('userId')
        exam_id = request.data.get('examId')
    
        if not user_id:
            return Response({"message": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
    
        if not exam_id:
            return Response({"message": "Exam ID is required."}, status=status.HTTP_400_BAD_REQUEST)
    
        user_collection = get_collection('auth_users')
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    
        try:
            exam_id_collection = get_collection("examId_db")
            result = exam_id_collection.delete_one({"_id": exam_id, "user_id": user_id})
        
            if result.deleted_count == 0:
                return Response({"message": "Exam ID not found or not authorized to delete."}, status=status.HTTP_404_NOT_FOUND)
        
            # Delete associated documents in course_pdf collection
            course_pdf_collection = get_collection("course_pdf")
            course_pdf_result = course_pdf_collection.delete_many({"exam_id": exam_id})
        
            # Delete associated documents in question_paper_db collection
            question_paper_collection = get_collection("question_paper_db")
            question_paper_result = question_paper_collection.delete_many({"exam_id": exam_id})
        
            return Response({
                "message": "Exam ID and associated documents deleted successfully.",
                "course_pdf_deleted_count": course_pdf_result.deleted_count,
                "question_paper_deleted_count": question_paper_result.deleted_count
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  

class ListOfDetailsUploadedAPI(APIView):
    def get(self, request):
        user_id = request.headers.get('userId')
        organization_id = request.headers.get('organizationId')
        
        if not user_id:
            return Response({"message": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not organization_id:
            return Response({"message": "Organization ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        user_collection = get_collection('auth_users')
        user = user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            question_db_collection = get_collection("question_db")
            questions = list(question_db_collection.find({"organization_id": organization_id, "user_id": user_id}))

            pdf_books_collection = get_collection("pdf_books")
            pdf_books = list(pdf_books_collection.find({"organization_id": organization_id, "user_id": user_id}))

            return Response({
                "questions": questions,
                "pdf_books": pdf_books
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # document list api
# class DocumentListAPI(APIView):
#     def get(self, request):
#         try:
#             user_id = request.headers.get("userId")
#             organization_id = request.headers.get("organizationId")
#             if not user_id:
#                 return Response(
#                     {"message": "User ID is required in the request header"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )
#             if not organization_id:
#                 return Response(
#                     {"message": "Organization ID is required in the request header"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             course_pdf_collection = get_collection('course_pdf')
#             question_paper_collection = get_collection('question_paper_db')
#             classes_collection = get_collection('classes')
#             sections_collection = get_collection('sections')
#             subjects_collection = get_collection('subjects')

#             data = {}
#             try:
#                 course_pdfs = course_pdf_collection.find({"organization_id": organization_id, "user_id": user_id})
#                 data["course_pdfs"] = [
#                     {
#                         "class_name": classes_collection.find_one({"_id": ObjectId(course_pdf.get("class_id"))}).get("name"),
#                         "subject_name": subjects_collection.find_one({"_id": ObjectId(course_pdf.get("subject"))}).get("name"),
#                         "section_name": sections_collection.find_one({"_id": ObjectId(course_pdf.get("section"))}).get("name"),
#                         "pdf_file_url": course_pdf.get("pdf_file_path"),
#                         "user_id": user_id,
#                         "organization_id": organization_id
#                     }
#                     for course_pdf in course_pdfs
#                 ]
#             except Exception as e:
#                 data["course_pdfs_error"] = str(e)
                
#             try:
#                 question_papers = question_paper_collection.find({"organization_id": organization_id, "user_id": user_id})
#                 data["question_papers"] = [
#                     {
#                         "class_name": classes_collection.find_one({"_id": ObjectId(question_paper.get("class_id"))}).get("name"),
#                         "subject_name": subjects_collection.find_one({"_id": ObjectId(question_paper.get("subject"))}).get("name"),
#                         "section_name": sections_collection.find_one({"_id": ObjectId(question_paper.get("section"))}).get("name"),
#                         "pdf_file_url": question_paper.get("question_file_url"),
#                         "user_id": user_id,
#                         "organization_id": organization_id
#                     }
#                     for question_paper in question_papers
#                 ]
#             except Exception as e:
#                 data["question_papers_error"] = str(e)

#             return Response(data, status=status.HTTP_200_OK)

        
#         except Exception as e:
#             return Response(
#                 {"message": "An unexpected error occurred while fetching data", "error": str(e)},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )


class DocumentListAPI(APIView):
    def get(self, request):
        try:
            exam_id = request.headers.get("examId")
            organization_id = request.headers.get("organizationId")
            if not exam_id:
                return Response(
                    {"message": "Exam ID is required in the request header"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not organization_id:
                return Response(
                    {"message": "Organization ID is required in the request header"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                exam_id_collection = get_collection('examId_db')
                exam_record = exam_id_collection.find_one({"_id": exam_id})
                if not exam_record:
                    return Response(
                        {"message": "Invalid exam ID or exam record not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            except Exception as e:
                 return Response(
                        {"message": "Invalid exam ID or exam record not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                

            user_id = exam_record.get("user_id")
            if not user_id:
                return Response(
                    {"message": "User ID not found in the exam record"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            try:
                course_pdf_collection = get_collection('course_pdf')
                question_paper_collection = get_collection('question_paper_db')
                classes_collection = get_collection('classes')
                sections_collection = get_collection('sections')
                subjects_collection = get_collection('subjects')
            except Exception as e:
                return Response(
                    {"message": "Error fetching collections", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            data = {}

            try:
                course_pdfs = course_pdf_collection.find({"organization_id": organization_id})
                data["course_pdfs"] = [
                    {
                        "class_name": classes_collection.find_one({"_id": ObjectId(course_pdf.get("class_id"))}).get("name"),
                        "subject_name": subjects_collection.find_one({"_id": ObjectId(course_pdf.get("subject"))}).get("name"),
                        "section_name": sections_collection.find_one({"_id": ObjectId(course_pdf.get("section"))}).get("name"),
                        "pdf_file_url": course_pdf.get("pdf_file_path"),
                        "organization_id": organization_id,
                        "question_uploaded": exam_record.get("question_uploaded", False),
                        "is_active": exam_record.get("is_active", False),
                    
                        
                    }
                    for course_pdf in course_pdfs
                ]
            except Exception as e:
                data["course_pdfs_error"] = str(e)

            try:
                question_papers = question_paper_collection.find({"organization_id": organization_id})
                data["question_papers"] = [
                    {
                        "class_name": classes_collection.find_one({"_id": ObjectId(question_paper.get("class_id"))}).get("name"),
                        "subject_name": subjects_collection.find_one({"_id": ObjectId(question_paper.get("subject"))}).get("name"),
                        "section_name": sections_collection.find_one({"_id": ObjectId(question_paper.get("section"))}).get("name"),
                        "pdf_file_url": question_paper.get("question_file_url"),
                        "organization_id": organization_id,
                        
                        "course_uploaded":exam_record.get("course_uploaded" ,False),
                        "is_active": exam_record.get("is_active", False),
                        
                    }
                    for question_paper in question_papers
                ]
                if not  question_papers:
                    data["question_papers"] = "Question paper is not uploaded by the org/user"
                # else:
                #      data["question_papers"] = "Question paper is not uploaded by the org/user"

            except Exception as e:
                data["question_papers_error"] = str(e)
            # if not data.get("question_papers"):
            #     data["question_papers"] = "Question paper is not uploaded by the org/user"

            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"message": "An unexpected error occurred while fetching data", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )