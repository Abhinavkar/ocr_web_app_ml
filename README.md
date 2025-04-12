SET UP & INSTALL SWE BACKEND CODE

Step 1  : Create a Separate folder 
Step 2  :  IDE Terminal clone the repo using this command :-
              git clone https://github.com/Abhinavkar/ocr_web_app_ml.git


Step 3  : Create a Virtual Environment using this command
 pip install virtualenv
python3  -m venv venv

Step 4  : To Activate the virtual environment
On macOS/Linux: source venv/bin/activate
On Windows : venv\Scripts\activate

Step 5  : After activating the virtual environment install the dependencies

pip install -r requirements.txt 


Step 6 : In the main folder create a ( .env file )
             In that file mention the API KEYS & BUCKET details
             

ASK ADMINISTRATOR FOR .ENV FILE 



Step 7 : To run the backend server 
              python3 manage.py runserver ( running the backend server )


SET UP & INSTALL SWE FRONTEND CODE


Step 1 : Create another folder separately 

Step 2  : In IDE Terminal clone the repo using this command :-
              git clone https://github.com/Abhinavkar/ocr_fe.git

Step 3 : Install the node ( sudo apt install nodejs npm -y ) using this command

Step 4 : Run through this command 
             npm i     ( for installing packages )
             npm run dev ( for running the frontend server )



