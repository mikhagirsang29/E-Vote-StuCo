from locust import HttpUser, task, between
import random

# Generate 200 dummy student IDs in the app DB before running this test.
# Example IDs: testuser1, testuser2, ..., testuser200 with the same password.
dummy_students = [f"testuser{i}" for i in range(1, 1001)]

class StudentVoter(HttpUser):
    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.student_id = dummy_students.pop(0) if dummy_students else None
        self.password = "password"  # Update this if your dummy accounts use a different password
        self.has_voted = False

        if self.student_id:
            self.client.post("/login", data={
                "student_id": self.student_id,
                "password": self.password
            })

    @task
    def cast_vote(self):
        if not self.student_id or self.has_voted:
            return

        chosen_candidate = random.choice([1, 2, 3])  # adjust candidate IDs as needed
        with self.client.post("/vote", data={"candidate_id": chosen_candidate}, catch_response=True) as response:
            if response.status_code == 200 and "already voted" not in response.text.lower():
                self.has_voted = True
                response.success()
            else:
                response.failure("Vote failed or duplicate")
