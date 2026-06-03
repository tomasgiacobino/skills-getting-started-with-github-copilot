"""
Comprehensive integration tests for the Mergington High School Activities API.
"""

import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """GET /activities should return a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_all_activities(self, client):
        """GET /activities should return all activities in the database"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Soccer Team",
            "Swimming Club", "Art Club", "Drama Club", "Debate Team", "Math Olympiad"
        ]
        
        assert len(activities) == 9
        for activity_name in expected_activities:
            assert activity_name in activities
    
    def test_get_activities_returns_correct_structure(self, client):
        """GET /activities should return activities with correct structure"""
        response = client.get("/activities")
        activities = response.json()
        
        # Check one activity to verify structure
        chess_club = activities["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_get_activities_shows_current_participants(self, client):
        """GET /activities should show currently registered participants"""
        response = client.get("/activities")
        activities = response.json()
        
        chess_club = activities["Chess Club"]
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]
    
    def test_get_activities_shows_empty_participants(self, client):
        """GET /activities should show empty participant list for new activities"""
        response = client.get("/activities")
        activities = response.json()
        
        soccer_team = activities["Soccer Team"]
        assert soccer_team["participants"] == []


class TestRootRedirect:
    """Tests for the GET / endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """GET / should redirect to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Successfully sign up for an activity"""
        response = client.post(
            "/activities/Soccer%20Team/signup",
            params={"email": "john.doe@mergington.edu"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "john.doe@mergington.edu" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Signing up should add participant to the activity"""
        client.post(
            "/activities/Swimming%20Club/signup",
            params={"email": "alex.smith@mergington.edu"}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert "alex.smith@mergington.edu" in activities["Swimming Club"]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """Signing up for non-existent activity should return 404"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_registered(self, client):
        """Signing up twice for the same activity should return 400"""
        email = "test@mergington.edu"
        
        # First signup
        client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        
        # Second signup with same email
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_students_same_activity(self, client):
        """Multiple students should be able to sign up for the same activity"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                "/activities/Art%20Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all students were added
        response = client.get("/activities")
        activities = response.json()
        art_club_participants = activities["Art Club"]["participants"]
        
        for email in emails:
            assert email in art_club_participants
    
    def test_signup_respects_max_participants(self, client):
        """Signup should still work without enforcing max_participants limit"""
        # This test documents current behavior - the API doesn't enforce capacity limits
        response = client.get("/activities")
        gym_class = response.json()["Gym Class"]
        initial_count = len(gym_class["participants"])
        
        # Try to add one more participant
        response = client.post(
            "/activities/Gym%20Class/signup",
            params={"email": "new.student@mergington.edu"}
        )
        
        # Currently succeeds (no capacity enforcement)
        assert response.status_code == 200


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Successfully unregister from an activity"""
        email = "michael@mergington.edu"
        
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Unregistering should remove participant from the activity"""
        email = "michael@mergington.edu"
        
        # Verify participant exists before unregister
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        assert email in chess_club["participants"]
        
        # Unregister
        client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]
        assert email not in chess_club["participants"]
    
    def test_unregister_activity_not_found(self, client):
        """Unregistering from non-existent activity should return 404"""
        response = client.delete(
            "/activities/Fake%20Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered(self, client):
        """Unregistering when not signed up should return 400"""
        response = client.delete(
            "/activities/Soccer%20Team/unregister",
            params={"email": "not.registered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_from_empty_activity(self, client):
        """Unregistering from activity with no participants should return 400"""
        response = client.delete(
            "/activities/Art%20Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == 400
    
    def test_unregister_then_signup_again(self, client):
        """A student should be able to sign up again after unregistering"""
        email = "daniel@mergington.edu"
        
        # Start: Daniel is in Chess Club
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        response = client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        
        # Sign up again
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify re-added
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
    
    def test_unregister_multiple_participants_same_activity(self, client):
        """Unregistering one participant shouldn't affect others"""
        # Programming Class has emma and sophia
        response = client.get("/activities")
        prog_class = response.json()["Programming Class"]
        assert "emma@mergington.edu" in prog_class["participants"]
        assert "sophia@mergington.edu" in prog_class["participants"]
        
        # Unregister Emma
        client.delete(
            "/activities/Programming%20Class/unregister",
            params={"email": "emma@mergington.edu"}
        )
        
        # Verify Emma is gone but Sophia remains
        response = client.get("/activities")
        prog_class = response.json()["Programming Class"]
        assert "emma@mergington.edu" not in prog_class["participants"]
        assert "sophia@mergington.edu" in prog_class["participants"]
