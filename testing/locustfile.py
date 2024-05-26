from locust import HttpUser, task, between
import random

class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
    queries = [
        "What is BCG?",
        "What are sustainability objectives in the report?",
        "Summarize the BCG's social impact.",
        "What are the values of BCG?",
        "What was the vision and impact in 2022?"
    ]

    @task
    def load_query(self):
        query = random.choice(self.queries)
        self.client.post("/query/", data={"query": query})