from fastapi import APIRouter, Response
from services.papers_with_code_service import PapersWithCodeService
from config.config import PAPERS_DATA_DIR_PATH, PAPERS_DATA_FILE, LINKS_CODE_PAPERS_FILE
from models.result import Result

papers_with_code = PapersWithCodeService(PAPERS_DATA_DIR_PATH, PAPERS_DATA_FILE, LINKS_CODE_PAPERS_FILE)
router = APIRouter()

# Get papers
@router.get('/papers-with-code', status_code = 200)
def get_papers_with_code(response: Response, search_query: str = '', page_number: int = 1, results_per_page: int = 10) -> Result:
    try:
        papers = PapersWithCodeService.get_joined_papers(
            joined_papers_dataframe = papers_with_code.df_papers_with_code_links_joined, 
            search_query = search_query, 
            page_number = page_number, 
            results_per_page = results_per_page
        )

        return Result(
            Result.SUCCESS,
            'Successfully loaded papers',
            papers
        ).to_dict()
    except:
        result = Result(
            Result.FAIL,
            'An error occurred while retrieving papers',
            Result.EXCEPTION
        )
        response.status_code = result.get_status_code()
        return result.to_dict()

# Get paper by ID
@router.get('/papers-with-code/{paper_id}', status_code = 200)
def get_paper_by_id(paper_id: str, response: Response) -> Result:
    try:
        paper = PapersWithCodeService.get_paper_by_id(
            joined_papers_dataframe = papers_with_code.df_papers_with_code_links_joined, 
            paper_id = paper_id
        )

        return Result(
            Result.SUCCESS,
            'Successfully retrieved paper',
            paper
        ).to_dict()
    except Exception:
        result = Result(
            Result.FAIL,
            'An error occurred while retrieving paper',
            Result.EXCEPTION
        )
        response.status_code = result.get_status_code()
        return result.to_dict()