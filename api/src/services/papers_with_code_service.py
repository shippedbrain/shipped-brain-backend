from datetime import datetime, date
from pandas.core.frame import DataFrame
import json
import pandas as pd
import os
import requests

PAPERS_WITH_CODE_URL: str = 'https://paperswithcode.com/paper/'
PAPERS_WITH_CODE_DOWNLOAD_URL: str = "https://paperswithcode.com/media/about/"

class PapersWithCodeService:
    def __init__(self, data_dir_path: str, papers_data: str, links_code_papers_data: str, ) -> None:
        """ Load data from papers with code


        :param data_dir_path: path papers data
        :param papers_data: file with papers data in [data_dir_path]; 
                            name must be the same as in the one dowloaded from [PAPERS_WITH_CODE_DOWNLOAD_URL]
        :param links_code_papers_data: file with repos links to papers data in [data_dir_path]; 
                            name must be the same as in the one dowloaded from [PAPERS_WITH_CODE_DOWNLOAD_URL]
        """
        papers_data_abs_path = os.path.join(data_dir_path, papers_data)
        links_code_papers_data_abs_path = os.path.join(data_dir_path, links_code_papers_data)
        
        # Download data
        if not os.path.exists(papers_data_abs_path):
            PapersWithCodeService._download_file(PAPERS_WITH_CODE_DOWNLOAD_URL, papers_data, data_dir_path)

        if not os.path.exists(links_code_papers_data_abs_path):
            PapersWithCodeService._download_file(PAPERS_WITH_CODE_DOWNLOAD_URL, links_code_papers_data, data_dir_path)

        try:
            self.df_papers = pd.read_json(papers_data_abs_path, compression="gzip").sort_values('date', kind="mergesort", ascending=False)
            self.df_links_code_papers = pd.read_json(links_code_papers_data_abs_path, compression="gzip")
            self.df_papers_with_code_links_joined = pd.merge(self.df_papers, self.df_links_code_papers, on="paper_url", how="left")
        except:
            print("[ERROR] Could not read papers. Check if files exist")

    @staticmethod
    def _download_file(base_url, file_name, data_dir_path):
        # TODO handle exception - raise exception?
        try:
            if not os.path.exists(data_dir_path):
                os.mkdir(data_dir_path)
        except Exception as e:
            print(f"[EXCEPTION] Failed to create '{data_dir_path}' directory. Error: {e}")

        try:
            papers_data_url = os.path.join(base_url, file_name)
            target = os.path.join(data_dir_path, file_name)

            print(f"[INFO] Downlaoding {papers_data_url}...")

            download = requests.get(papers_data_url)
            with open(target, "wb") as f:
                f.write(download.content)
        except Exception as e:
            print(f"[EXCEPTION] An error occurred while trying to dowload file from '{papers_data_url}' or save data to {target}.  Error: {e}")
    
    @staticmethod
    def get_paper_id(paper_url: str) -> str:
        ''' Splits paper url and returns unique ID

        :param paper_url: Paper's URL
        :return: Paper's ID
        '''

        return paper_url.split(PAPERS_WITH_CODE_URL)[1]

    @staticmethod
    def get_paper_published_date(paper_timestamp: int) -> date:
        ''' Converts timestamp from paper's date to user friendly data format

        :param paper_timestamp: Paper's published timestamp
        :return: Date in YYYY-MM-DD format
        '''

        return datetime.fromtimestamp(paper_timestamp / 1000.0).date()

    @staticmethod
    def get_joined_papers(joined_papers_dataframe: DataFrame, search_query: str = '', page_number: int = 1, results_per_page: int = 10) -> list:
        ''' Gets paginated joined papers

        :param joined_papers_dataframe: Joined PapersWithCode pandas' dataframe
        :param search_query: Search query used to filter papers
        :param page_number: Page to fetch
        :param results_per_page: Number of results to return
        :return: List of papers
        '''

        offset = results_per_page * page_number - results_per_page

        # Search
        papers = joined_papers_dataframe[joined_papers_dataframe['title'] == search_query] if search_query != '' else joined_papers_dataframe
        # Paginate
        papers = papers[offset:offset + results_per_page] if page_number > 1 else papers.head(results_per_page)
        papers = json.loads(papers.to_json(orient='records'))

        # Set paper ID and user friendly date
        for paper in papers:
            paper['paper_id'] = PapersWithCodeService.get_paper_id(paper['paper_url'])
            paper['published_at'] = PapersWithCodeService.get_paper_published_date(paper['date'])

        return papers

    @staticmethod
    def get_paper_by_id(joined_papers_dataframe: DataFrame, paper_id: str) -> dict:
        ''' Gets paper by ID

        :param joined_papers_dataframe: Joined PaperWithCode pandas' dataframe
        :param paper_id: Paper ID
        :return: Single paper dict
        '''

        paper = json.loads(joined_papers_dataframe.loc[joined_papers_dataframe['paper_url'] == (PAPERS_WITH_CODE_URL + paper_id)].to_json(orient='records'))

        if len(paper) > 0:
            paper = paper[0]

        # Set paper ID and user friendly date
        if paper is not None:
            paper['paper_id'] = PapersWithCodeService.get_paper_id(paper['paper_url'])
            paper['published_at'] = PapersWithCodeService.get_paper_published_date(paper['date'])

        return paper