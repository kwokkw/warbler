# QUESTIONS

-   `models.py`: The `unique=True` constraint in the `likes` table

    -   How each message can only be liked once by preventing duplicate entries in the database?

        -   Can't multiple users like one single message?

        -   When a user attempts to like a message, a new entry is created in the `likes` table linking the user's `user_id` with the `message_id`.
        -   If the same user tries to like the same message again, the attempt to insert a new record with the same `message_id` will violate the unique constraint, leading to a database error
            -   What about a different user tries to like the message that has been already liked?

-   Part Three: Add Tests

    -   Following the instruction, we should set `FLASK_ENV` to `production`, so it does not use debug mode, and therefore won't use the Debug Toolbar during our tests. 

        -   The question is, what is the difference between setting `FLASK_ENV=production` and `app.config['TESTING'] = True`.

# Visualization of Self-Referential Many-to-Many Relationship

In the `Warbler` app, users can follow each other, which creates a **many-to-many relationship**. This is accomplished using a **self-referential relationship**, where the `User` table references itself through an association table (`Follows`).

## Tables Involved

### 1. **User** Table
| id  | username | email               |
| --- | -------- | --------------------|
| 1   | alice    | alice@example.com   |
| 2   | bob      | bob@example.com     |
| 3   | charlie  | charlie@example.com |

The `User` table stores the basic information about users.

### 2. **Follows** Table (Association Table)
| user_being_followed_id | user_following_id |
| ---------------------- | ----------------- |
| 2                      | 1                 |
| 3                      | 1                 |
| 1                      | 2                 |

The `Follows` table acts as a bridge between users. It contains two foreign keys:
- `user_being_followed_id`: The ID of the user being followed.
- `user_following_id`: The ID of the user doing the following.

## Relationships

### 1. **Followers** Relationship (Who follows the current user?)
```py
followers = db.relationship(
    "User",
    secondary="follows",
    primaryjoin=(Follows.user_being_followed_id == id),
    secondaryjoin=(Follows.user_following_id == id)
)
```

### Following Relationship (Who is the current user following?)
```py
following = db.relationship(
    "User",
    secondary="follows",
    primaryjoin=(Follows.user_following_id == id),
    secondaryjoin=(Follows.user_being_followed_id == id)
)

```
### Diagram (followers)

    ┌─────────────┐              ┌─────────────┐
    │  User       │              │  Follows    │
    │─────────────│              │─────────────│
    │ id          │<─────────────┤ user_being  │
    │ username    │ ──primary──► │ followed_id │
    └─────────────┘              |             |
                                 │─────────────│
    ┌─────────────┐              |             |
    │  User       │              │  Follows    │
    │─────────────│ ◄─secondary──┤ user_follow │
    │ id          │ ────────────►│ _ing_id     │
    │ username    │              |             |
    └─────────────┘              └─────────────┘


### How It Works

- **Followers**: For each user, the `primaryjoin` finds entries in the `Follows` table where the user is being followed, and the `secondaryjoin` finds the users who are following them.

- **Following**: The `primaryjoin` finds entries where the user is following someone, and the `secondaryjoin` finds who is being followed.

# Database Schema Diagram

## Tables:
- **users**
- **follows**
- **messages**
- **likes**

### users
| Column Name        | Type      | Constraints         |
|--------------------|-----------|---------------------|
| id                 | Integer   | Primary Key         |
| email              | Text      | Not Null, Unique    |
| username           | Text      | Not Null, Unique    |
| image_url          | Text      | Default             |
| header_image_url   | Text      | Default             |
| bio                | Text      |                     |
| location           | Text      |                     |
| password           | Text      | Not Null            |

### messages
| Column Name   | Type        | Constraints            |
|---------------|-------------|------------------------|
| id            | Integer     | Primary Key            |
| text          | String(140) | Not Null               |
| timestamp     | DateTime    | Not Null, Default Now  |
| user_id       | Integer     | Foreign Key (users.id) |

### follows
| Column Name               | Type       | Constraints                         |
|---------------------------|------------|-------------------------------------|
| user_being_followed_id     | Integer   | Foreign Key (users.id), Primary Key |
| user_following_id          | Integer   | Foreign Key (users.id), Primary Key |

### likes
| Column Name   | Type      | Constraints                       |
|---------------|-----------|-----------------------------------|
| id            | Integer   | Primary Key                       |
| user_id       | Integer   | Foreign Key (users.id)            |
| message_id    | Integer   | Foreign Key (messages.id), Unique |

## Relationships:

1. **users -> messages**:  
   One-to-Many relationship.  
   Each user can have multiple messages, but each message is linked to only one user (`user_id` in `messages` table).

2. **users -> follows (self-referential many-to-many)**:  
   A many-to-many relationship.  
   Users can follow multiple other users and be followed by multiple users. This is done through the `follows` table which uses two foreign keys (`user_being_followed_id` and `user_following_id`).

3. **users -> likes -> messages**:  
   A many-to-many relationship.  
   A user can like multiple messages, and a message can be liked by multiple users. The `likes` table connects the `users` and `messages` tables via `user_id` and `message_id`.

# Research and Understand Login Strategy

## How is the logged in user being kept track of?

The Flask `g` object is used to keep track of a logged-in user. 

## What is Flask’s `g` object?

Flaks's `g` object is a global namespace object for temporary storing and sharing  data during a single request. The data stored in `g` is only available for the duration of a request and will be cleared after the request ends. 

## What is the purpose of `add_user_to_g` ?

The purpose of it is checking if user is logged in and store the user in the `g` object. 

## What does `@app.before_request` mean?

The `@app.before_request` decorator defines a function that runs before any request is handled. 