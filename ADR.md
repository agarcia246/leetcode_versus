## [1]. DATABASE DESIGN 
Date: 2026-09-29
Status: Decided
Context: I decided to start this project by building my database schema. Once I have a clear view of all the data that I want to manage, I can then start connecting everything together.
Decision: For my project, what I decided to do was to have a central table which would handle all the sessions and stuff, called rooms. Then, I'd have some smaller tables called players, problems, submissions, and topics which would provide some like extra data relating to the relating to the session. Finally, we'd have some, some joining tables, which are room_problems, room_players, and problem_topics which connect the, the many to many relationships between the tables
Alternatives considered: At one point I wanted to get rid of the problem_topics table because I felt that it would be simpler to just store topics as a long string in the problems table. In the end I decided against this because since the data would be repeated a lot since a lot of the problem share the same topics it's  better to just make a join table
Consequences:  know that I have my database design. I can finally move forward and start building the API and the rest of the app. Since I already know how my data will be structured it's easier to find out how to connect it to the user.


