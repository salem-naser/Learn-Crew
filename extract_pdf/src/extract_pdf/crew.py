from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from extract_pdf.tools.custom_tool import PDFExtractorTool, JSONValidatorTool, APIPostTool


@CrewBase
class ExtractPdf():
    """ExtractPdf crew"""

    agents: List[BaseAgent]
    tasks: List[Task]


    @agent
    def pdf_extractor(self) -> Agent:
        return Agent(
            config=self.agents_config['pdf_extractor'], # type: ignore[index]
            verbose=True,
            tools=[PDFExtractorTool()]
        )

    @agent
    def data_mapping_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['data_mapping_specialist'], # type: ignore[index]
            verbose=True
        )

    @agent
    def api_integration_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['api_integration_agent'], # type: ignore[index]
            verbose=True,
            tools=[JSONValidatorTool(), APIPostTool()]
        )

    @task
    def extract_pdf_task(self) -> Task:
        return Task(
            config=self.tasks_config['extract_pdf_task'], # type: ignore[index]
        )

    @task
    def map_to_api_schema_task(self) -> Task:
        return Task(
            config=self.tasks_config['map_to_api_schema_task'], # type: ignore[index]
            output_file='formatted_data.json'
        )

    @task
    def validate_json_task(self) -> Task:
        return Task(
            config=self.tasks_config['validate_json_task'], # type: ignore[index]
        )

    @task
    def post_to_api_task(self) -> Task:
        return Task(
            config=self.tasks_config['post_to_api_task'], # type: ignore[index]
            output_file='api_response.json'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ExtractPdf crew"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
