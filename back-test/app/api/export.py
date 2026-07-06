# import os

# from fastapi import APIRouter
# from fastapi.responses import FileResponse

# from app.services.export_service import ExportService

# router = APIRouter(
#     prefix="/export",
#     tags=["Export"]
# )


# @router.get("/top10-high")

# def download_csv():

#     path = ExportService.export_top10_high()

#     if path is None:

#         return {
#             "message": "No Data Found"
#         }

#     return FileResponse(

#         path,

#         media_type="text/csv",

#         filename=os.path.basename(path)

#     )

import os

from fastapi import APIRouter
from fastapi.responses import FileResponse
from fastapi import HTTPException

from app.services.export_service import ExportService

router = APIRouter(
    prefix="/export",
    tags=["Export"]
)


@router.get("/top10-high")

def download_csv():

    path = ExportService.export_top10_high()

    if path is None:
        raise HTTPException(
            status_code=404,
            detail="No Data Found"
        )

    return FileResponse(
        path,
        media_type="text/csv",
        filename=os.path.basename(path)
    )