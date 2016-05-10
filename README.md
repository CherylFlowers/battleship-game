
# Battleship Game API

Welcome to the Battleship Game API!

### Summary

The Battleship game doesn't have a GUI yet, it's your job to create one! The Battleship RESTful API provides you with several endpoints that are built using Google Cloud Endpoints. The API is hosted on Google App Engine. The endpoints provide you with the basics needed for a game including creating users, creating a game, making moves and scoring hits.

### Pre-requisites

 - Internet
 - Browser
 - A blank Google App Engine project
 - Development environment of your choice

### Setup Instructions
1. Update the application value in app.yaml to the app ID you have registered
 in the App Engine admin console.
2. Using the Google App Engine Launcher, deploy the application.
3. Using a browser navigate to <your app id>/_ah/api/explorer.

### API Endpoint Methods

#### cancel_game
 - Path: 'cancelGame'
 - Method: POST
 - Parameters: websafe_game_key
 - Returns: Message confirming the game was cancelled.
 - Description: Cancel a game in progress. Will return a warning message if game is already cancelled. Will return a warning message if game is already finished (cannot cancel).

#### create_user
 - Path: 'createUser'
 - Method: POST
 - Parameters: username
 - Returns: Message confirming creation of the User and the user key.
 - Description: Creates a new user. The username is required and must be unique. Will raise a conflict exception for a duplicate username.

#### get_game
 - Path: 'getGame'
 - Method: GET
 - Parameters: websafe_game_key
 - Returns: Returns the current state of the game ie. Username : Hits 3 : Miss 12 : Sunk 0
 - Description: Returns the number of hits, number of misses and number of sunk boats for each user in a particular game.

#### get_game_history
 - Path: 'getGameHistory'
 - Method: GET
 - Parameters: websafe_game_key
 - Returns: A list of all moves for a game.
 - Description: View the history of a game, move by move.

#### get_user_boats
 - Path: 'getUserBoats'
 - Method: GET
 - Parameters: websafe_game_key, websafe_user_key
 - Returns: Get a list of a users' boat coordinates for a game.
 - Description: View a list of all boats for a user in a particular game.

#### get_user_games
 - Path: 'getUserGames'
 - Method: GET
 - Parameters: websafe_user_key
 - Returns: All active games for a user.
 - Description: View a list of all games that are currently active for a user.

#### get_user_rankings
 - Path: 'getUserRankings'
 - Method: GET
 - Parameters: None
 - Returns: A list of users ordered by wins/losses.
 - Description: View a list of the overall standings of all users. Users who have not played a game are not included in this list.

#### get_user_score
 - Path: 'getUserScore'
 - Method: GET
 - Parameters: websafe_user_key
 - Returns: The number of games that a user has won and lost.
 - Description: View how well a particular user is doing. This endpoint is similar to get_user_rankings, however it only returns data for a single user.

#### make_move
 - Path: 'makeMove'
 - Method: GET
 - Parameters: websafe_game_key, websafe_user_key, row, col
 - Returns: A status message (miss, duplicate, hit, sunk, won)
 - Description: Enter a move for a user for a game. The endpoint will indicate if the move was a: hit, miss, duplicate move, boat sunk and game won.

#### new_game
 - Path: 'newGame'
 - Method: POST
 - Parameters: websafe_username1_key, websafe_username2_key
 - Returns: A message indicating that a game has been created and the game key.
 - Description: Once users have been created, use this endpoint to start a game. The endpoint will automatically create boats for each user.

### Getting Started - Simple Example Game

1. First, create some users; Harry and Sally.
`create_user`

2. Using the user keys from step 1, create a new game for those users.
`new_game`

3. View the list of boats for a user. Use the game key from step 2 and the user key from step 1.
`get_user_boats`

4. Using the game key from step 2 and the user key from step 1, log a move for Sally.
`make_move`

5. Log a move for Harry.
`make_move`

6. Repeat steps 4 and 5 until a winner is declared. 
 
During the game you can use any of the following endpoints to check the status:
`get_game` -- List the total number of hits, total number of misses and total number of sunk boats for each user.
`get_game_history` -- List all moves in the game (in order).

You can also use the `cancel_game` endpoint to cancel a game that's in progress.

7. After multiple users have been entered and multiple games have been played, you can use any of the following endpoints to check the individual user standings or the standings for all users:
`get_user_games` -- List of all games for a user that are In Progress (0) or Finished (1).
`get_user_rankings` -- List of all users ordered by wins and losses.
`get_user_score` -- The wins and losses for a single user.

