Project introduction:
For this project, my idea was to build a game where players can face off against each other in leetcode competitions 



Tech Stack:

- Frontend
    - react static pages served from the api
- Backend:
    - FastAPI
- Database:
    - SQLite
- APIS: 
    - Leetcode Graphql API

Database design:
-the data


API Design:
POST /api/rooms
    - What does it do: 
        1. checks that the username given exists in leetcode and adds the user to the players table. 
        2. based on the user's filters obtains the questions from the leetcode graphql api and adds them to problem and problem_topic tables
        3. Creates room with the following data in the room table of the db:
            a. room_code: a random 6 digit alphanumerical that marks the room so that others can join
            b. status: initially set to created. Marks the current state of the room (created, started, finished, inactive)
            c. start_time: marks the time that the room was created
            d. host: username of the user that created the room

        the user's will then be redirected to room/code and their username will be stored in their local storage

GET /api/rooms/[code]
    - runs every 5 seconds
    - what does it do:
        - makes an api call the leetcode user to each of the users in the room
        - obtains a list of their past 5 submissions
        - if any of the names of those submissions matches the one of the active problems of the room it records them in the submissions table
        - if
        

POST /api/rooms/[code]/join
    - 
GET /api/rooms/[code]/start



AI DISCLAIMER:
