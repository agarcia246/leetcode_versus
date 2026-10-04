from pydantic import BaseModel
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Text,
)



from sqlalchemy.orm import relationship

from database import Base





# Database Models
class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lc_user = Column(String, nullable=False, unique=True)

    hosted_rooms = relationship("Room", back_populates="host")
    room_links = relationship("RoomPlayer", back_populates="player")
    submissions = relationship("Submission", back_populates="player")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    room_code = Column(String, nullable=False, unique=True)

    host_id = Column(Integer, ForeignKey("players.id"), nullable=False)

    current_status = Column(
        String,
        nullable=False,
        default="Created"
    )

    duration_min = Column(Integer, nullable=False, default=30)

    creation_time = Column(Text, nullable=False)
    start_time = Column(Text)
    end_time = Column(Text)

    last_polled_at = Column(Text)
    poll_error = Column(Text)

    __table_args__ = (
        CheckConstraint(
            "current_status IN ('Created', 'Active', 'Inactive', 'Finished')",
            name="check_room_status"
        ),
    )

    host = relationship("Player", back_populates="hosted_rooms")
    submissions = relationship("Submission", back_populates="room")
    room_players = relationship("RoomPlayer", back_populates="room")
    room_problems = relationship("RoomProblem", back_populates="room")


class Problem(Base):
    __tablename__ = "problems"

    id = Column(Integer, primary_key=True, autoincrement=True)

    title = Column(String, nullable=False)

    lc_id = Column(String, nullable=False, unique=True)

    lc_url = Column(String, nullable=False)

    difficulty = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('Easy', 'Medium', 'Hard')",
            name="check_problem_difficulty"
        ),
    )

    submissions = relationship("Submission", back_populates="problem")
    room_problems = relationship("RoomProblem", back_populates="problem")
    topic_links = relationship("ProblemTopic", back_populates="problem")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False
    )

    player_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False
    )

    problem_id = Column(
        Integer,
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False
    )

    submitted_at = Column(Text, nullable=False)

    current_status = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "current_status IN ('Accepted', 'Wrong_Answer', 'Time_Limit', 'Pending')",
            name="check_submission_status"
        ),
    )

    room = relationship("Room", back_populates="submissions")
    player = relationship("Player", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True)

    topic_name = Column(String, nullable=False, unique=True)

    problem_links = relationship("ProblemTopic", back_populates="topic")


class RoomProblem(Base):
    __tablename__ = "room_problems"

    id = Column(Integer, primary_key=True, autoincrement=True)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False
    )

    problem_id = Column(
        Integer,
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False
    )

    display_order = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("room_id", "problem_id"),
        UniqueConstraint("room_id", "display_order"),
    )

    room = relationship("Room", back_populates="room_problems")
    problem = relationship("Problem", back_populates="room_problems")


class RoomPlayer(Base):
    __tablename__ = "room_players"

    id = Column(Integer, primary_key=True, autoincrement=True)

    room_id = Column(
        Integer,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False
    )

    player_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False
    )

    joined_at = Column(Text, nullable=False)

    score = Column(Integer, nullable=False, default=0)

    result = Column(
        String,
        nullable=False,
        default="Created"
    )

    __table_args__ = (
        UniqueConstraint("room_id", "player_id"),
        CheckConstraint(
            "result IN ('Created', 'In_Progress', 'Winner', 'Loser')",
            name="check_room_player_result"
        ),
    )

    room = relationship("Room", back_populates="room_players")
    player = relationship("Player", back_populates="room_links")


class ProblemTopic(Base):
    __tablename__ = "problem_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)

    problem_id = Column(
        Integer,
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False
    )

    topic_id = Column(
        Integer,
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint("problem_id", "topic_id"),
    )

    problem = relationship("Problem", back_populates="topic_links")
    topic = relationship("Topic", back_populates="problem_links")





# API



class CreateRoomModel(BaseModel):
    host_username:str
    duration:int
    problem_count:int
    difficulty:str
    topics:list[str]

class JoinRoomModel(BaseModel):
    username:str
    room_code:str


class StartRoomModel(BaseModel):
    player_id:str
    room_code:str


class GetRoomModel(BaseModel):
    room_code:str



class RoomStatus(str, enum.Enum):
    CREATED = "Created"
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    FINISHED = "Finished"