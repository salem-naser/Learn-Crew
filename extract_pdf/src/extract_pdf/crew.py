from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from extract_pdf.tools.custom_tool import (
    PDFExtractorTool,
    JSONValidatorTool,
    APIPostTool,
    FDALookupTool,
    GUIDExtractorTool
)


@CrewBase
class ExtractPdf():
    """ExtractPdf crew with two-endpoint workflow and FDA medication enrichment"""

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
    def medication_enrichment_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['medication_enrichment_agent'], # type: ignore[index]
            verbose=True,
            tools=[FDALookupTool()]
        )

    @agent
    def api_integration_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['api_integration_agent'], # type: ignore[index]
            verbose=True,
            tools=[JSONValidatorTool(), APIPostTool(), GUIDExtractorTool()]
        )

    @task
    def extract_pdf_task(self) -> Task:
        return Task(
            config=self.tasks_config['extract_pdf_task'], # type: ignore[index]
        )

    @task
    def map_to_user_schema_task(self) -> Task:
        return Task(
            config=self.tasks_config['map_to_user_schema_task'], # type: ignore[index]
            output_file='user_data.json'
        )

    @task
    def map_to_medication_schema_task(self) -> Task:
        return Task(
            config=self.tasks_config['map_to_medication_schema_task'], # type: ignore[index]
            output_file='medication_data_template.json'
        )

    @task
    def enrich_medication_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['enrich_medication_data_task'], # type: ignore[index]
            output_file='medication_data_enriched.json'
        )

    @task
    def validate_user_json_task(self) -> Task:
        return Task(
            config=self.tasks_config['validate_user_json_task'], # type: ignore[index]
        )

    @task
    def post_user_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['post_user_data_task'], # type: ignore[index]
            output_file='user_api_response.json'
        )

    @task
    def extract_user_guid_task(self) -> Task:
        return Task(
            config=self.tasks_config['extract_user_guid_task'], # type: ignore[index]
        )

    @task
    def prepare_medication_with_guid_task(self) -> Task:
        return Task(
            config=self.tasks_config['prepare_medication_with_guid_task'], # type: ignore[index]
            output_file='medication_data_final.json'
        )

    @task
    def validate_medication_json_task(self) -> Task:
        return Task(
            config=self.tasks_config['validate_medication_json_task'], # type: ignore[index]
        )

    @task
    def post_medication_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['post_medication_data_task'], # type: ignore[index]
            output_file='medication_api_response.json'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the ExtractPdf crew with two-endpoint medication workflow"""

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
