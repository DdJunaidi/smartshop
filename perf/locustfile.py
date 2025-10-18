from locust import HttpUser, task, between

class ApiUser(HttpUser):
    host = "http://localhost:8000"
    wait_time = between(1, 3)  # seconds

    @task(3)
    def recos(self):
        # hit a demo user id that exists; 1 is fine if your seed created it
        self.client.get("/api/recommendations/1/")

    @task(2)
    def search(self):
        self.client.get("/api/search", params={"q": "headphones"})


