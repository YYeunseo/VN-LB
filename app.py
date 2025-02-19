# 250214 upload

import streamlit as st
from PIL import Image
from io import BytesIO
from PIL import Image
import base64
import os
import json
from openai import OpenAI
import pandas as pd
from io import StringIO
import pdfplumber
import openai
from langchain_community.document_loaders import PyMuPDFLoader
from streamlit_pdf_viewer import pdf_viewer
import base64
import fitz
import time
from datetime import datetime, timedelta

#os.environ["OPENAI_API_KEY"] = "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"
os.environ["OPENAI_API_KEY"] = st.secrets["openai"]["OpenAI_key"]
#os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
st.set_page_config(layout="wide", page_title="Voronoi Label Studio🧑‍💻")

st.write("## 🧑‍💻 Clinical dataset LabelMate")
st.markdown(" **:blue-background[논문 PDF 파일]** 과 Efficacy table, Toxicity table, Dose table **:blue-background[표를 캡처해서 이미지 PNG]** 로 만들어 좌측 Sidebar에 넣어주세요.")
st.sidebar.write("## Upload Your Files :gear:")

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["Common", "Treat_info", "Patient_info", "Efficacy", "Toxicity", "PK_Common", "PK_Dose_independent", "PK_dosing info", "PK_measure"])

paper_pdf_upload = st.sidebar.file_uploader("Full Paper PDF format", type=["PDF"]) # 1개까지 허용
paper_efficacy_upload = st.sidebar.file_uploader("Efficacy Table PNG format", type=["PNG"], accept_multiple_files=True) # 3개까지 허용
paper_toxicity_upload = st.sidebar.file_uploader("Toxicity Table PNG format", type=["PNG"], accept_multiple_files=True) # 3개까지 허용
paper_dose_upload = st.sidebar.file_uploader("Dose info Table PNG format", type=["PNG"], accept_multiple_files=True) # 3개까지 허용

def check_column_headers(df1, df2):
    return list(df1.columns) == list(df2.columns)

def encode_image(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

def eff_pdf_to_text(upload):

    if upload is not None:
            start = time.time()
            file_bytes = upload.read()
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            full_text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                full_text += page.get_text()

            client = OpenAI()
            response_text = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"제공한 텍스트 자료에서 Abstract 문단 내용과 efficacy에 대해 설명하고 있는 모든 문단들을 가져와서 출력해줘. 텍스트 자료:{full_text}.",
                            },
                        ],
                    }
                ],
            )
            end = time.time()
            elapsed_time = end - start
            print(f"eff_pdf_to_text()에 걸린 시간: {elapsed_time} sec")

            related_text_input = response_text.choices[0].message.content
            print("최종 사용할 논문 본문 내용:\n", related_text_input)
            return related_text_input

def efficacy_table_image(upload):

    if upload:
        start = time.time()
        base64_image = encode_image(upload.read())
        client = OpenAI()
        response_replic = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """

                            **해야하는 일 **
                            제공된 이미지에 있는 표를 텍스트 표로 바꿔서 csv format으로 반환해줘. 추가 설명은 주지 말고 CSV 포멧 표만 반환해.
                            이때, 표에 함께 있는 caption 글을 csv format 맨 밑에 행에 함께 반환해줘. 행 누락 없이 모든 정보가 담겨야해. "정보 누락하지마"

                            **고려할 것**
                            행/열을 잘 구분하고, 이때 **띄어쓰기나 볼드체 등의 특징**을 보고, **상위 개념 하위 개념** 관계를 모두 파악하여 상위항목(예를 들어 Objective response rate)-하위항목(at 8 mo)으로 **합쳐서 행**으로 만들어줘.
                            수치가 **정확**하게 기입되어야해. 모르겠으면 빈칸으로 남겨두고, 확실한 것만 기입해. 가끔 윗 행과 아래 행의 수치를 바꿔서 적거나 새로 만드는 경우가 있더라. 헷갈리면 빈칸으로 냅둬.

                            """,
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
        )
        response_replic = response_replic.choices[0].message.content

        rows111 = response_replic.split("\n")
        data111 = [row.split(",") for row in rows111]
        df111 = pd.DataFrame(data111)
        df111 = df111.applymap(lambda x: x.replace('"', '') if isinstance(x, str) else x)

        end = time.time()
        elapsed_time = end - start
        print(f"efficacy_table_image()에 걸린 시간: {elapsed_time} sec")

        related_table_input = df111.to_csv(index=False)

        rows111 = related_table_input.split("\n")
        data111 = [row.split(",") for row in rows111]
        df111 = pd.DataFrame(data111)
        related_table_input = df111.applymap(lambda x: x.replace('"', '') if isinstance(x, str) else x)
        
        print("\n efficacy_table_image() 표 복제 출력:",related_table_input)
    else:
            related_table_input = None
    return related_table_input

def efficacy_table(related_table_input, related_text_input):

    start = time.time()
    client = OpenAI()
    response_our_excel = client.chat.completions.create(
      model="gpt-4o",
        messages=[
          {
              "role": "user",
              "content": f"""
              You will be given a CSV table as input. Your task is to transform this table into a new structured format based on the following strict rules:

              ### **Input Data Rules:**
              - The input is:
              ```
              {related_table_input}, {related_text_input} 만약 사용할 데이터가 없어도 열 헤더라도 만들어서 반환해.
              ```
              - **Do NOT modify, rephrase, summarize, omit, or alter any text, numbers, units, expressions, or symbols in any way.**
              - **Preserve full content, even if the text is long or contains commas, parentheses, or special characters.**
              - **Extract data exactly as it appears in the original table, maintaining full text integrity.**
              - Extract the correct values **by matching the row and column structure**, ensuring that all content from the relevant cells is fully retained.

              ### **Output Data Structure:**
              The output should be a new table with the following columns:
              ["treat_group", "sub_group", "no. patients", "category", "value_type", "value(#)","value(%)", "range_type", "range_low", "range_high"]
              Each column follows these strict rules:
              - **treat_group**: 어떤 그룹들의 효과를 비교한 표가 제공되었을거야. 여기어 그 그룹을 써야해. 용량 별 비교면 용량을 적고, 특정 약물을 투여한 집단이면 그 특정 약물이 되겠지. 제공된 table input에서 비교 대상을 쓰면 돼.
              - **sub_group**: treat_group에서 못다한 정보가 있을 때에 여기다가 작성해줘. 상위 그룹이 있거나 특별한 정보가 있을 경우.
              - **no. patients**: The total number of patients in each `sub_group`, extracted exactly as written (수치만 적어야해. 예를 들어, 총 환자 수가 몇 명인지를 N=10 이렇게 표시하지말고, 10이라고 적어.).
              - **category**: Extracted from row headers, containing treatment responses **exactly as written** (e.g., `"Progression-free survival†, Median (95% CI) — mo"`, including all symbols, punctuation, and formatting).
              - **value_type**: category의 축약어를 적는 열이야. 각 category마다 다음 옵션 중에서 해당하는 것이 있다면 적어주고, 없으면 빈칸으로 남겨두는 열이야. 다른 값은 쓰면 안되고, 아래 옵션에 해당하는 값만 입력해야해.
                                옵션: ORR, CR, PR, DC, SD, mPFS(m), OS(m), DoR(m), TTF(m), i_ORR, i_CR, i_PR, i_SD, i_mPFS (m), i_DoR (m). 
                                이때, 'best'라는 단어가 나오면 옵션 옆에 best_'를 붙여주면 돼. 예를 들어, catrgory가 'CNS activity||-Best response§-CR' 라면, value_type은 i_best_CR 인거야.
                                보통 CNS라는 단어가 나오면 'i_'를 붙이면 돼.

              - **Do NOT cut, truncate, or shorten this text in any way. The full row header must be preserved exactly as in the input.**
              - Check if the value represents a count (#) or a percentage (%), and categorize it accordingly as value (#) or value (%). mo의 경우 #에 적고, 그냥 수치인지 퍼센티지인지 구분해서 맞는 column에 넣어. metric은 적지 않아도 돼.
              - **Do NOT alter or remove units. If the cell contains multiple values, keep them together as a single string.**
              - **range_type**: Extract the confidence interval or range exactly as stated (e.g., `"95% CI"`).
              - **range_low** / **range_high**: Extract the exact minimum and maximum values from the range **without modification**.

              ### **Strict Output Rules:**
              - **Preserve all formatting, symbols, parentheses, spacing, commas, and special characters exactly as they appear in the input.**
              - **If a value includes a comma but was in a single cell in the original table, KEEP IT TOGETHER. Do NOT separate it into multiple columns.**
              - **Ensure that "category" contains the full original row header text without omission. DO NOT truncate long text.**
              - **DO NOT split, modify, or remove any part of the extracted data. Every cell must remain fully intact.**
              - **Return the final structured data in pure CSV format, with no additional text, explanations, or notes.**
              """
          }
      ]
  )

    print(response_our_excel)
    response_our_excel_data = response_our_excel.choices[0].message.content

    rows111 = response_our_excel_data.split("\n")
    data111 = [row.split(",") for row in rows111]
    df111 = pd.DataFrame(data111)
    df111 = df111.applymap(lambda x: x.replace('"', '') if isinstance(x, str) else x)

    header_idx = df111[df111[0] == 'treat_group'].index[0]
    df111.columns = df111.iloc[header_idx].values
    df_cleaned = df111.iloc[header_idx + 1:].reset_index(drop=True)
    end_idx = df_cleaned[df_cleaned.iloc[:, 0].str.contains('```', na=False)].index[0]
    efficacy_output = df_cleaned.iloc[:end_idx].reset_index(drop=True)

    if 'value(%)' in efficacy_output.columns:
        efficacy_output['value(%)'] = efficacy_output['value(%)'].str.replace('%', '', regex=False)

    if 'treat_group' in efficacy_output.columns and 'sub_group' in efficacy_output.columns:
        efficacy_output = efficacy_output.sort_values(by=['treat_group', 'sub_group'], ascending=[True, True]).reset_index(drop=True)

    end = time.time()
    elapsed_time = end - start
    print(f"efficacy_table_image()에 걸린 시간: {elapsed_time} sec")

    efficacy_output = efficacy_output.sort_values(by=['treat_group', 'sub_group'], ascending=[True, True]).reset_index(drop=True)
    return efficacy_output

def efficacy_add_table(eff_table1, eff_table2):
    if eff_table1 is not None and eff_table2 is not None: 
        if check_column_headers(eff_table1, eff_table2):
            efficacy_output = pd.concat([eff_table1, eff_table2], axis=0, ignore_index=True)
            return efficacy_output

    elif eff_table1 is not None and eff_table2 is None: 
            efficacy_output = eff_table1
            return efficacy_output

    else:
        efficacy_output = None
        return None


def tox_pdf_to_text(upload):

    if upload is not None:
            file_bytes = upload.read()
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            full_text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                full_text += page.get_text()

            client = OpenAI()
            response_text = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"제공한 텍스트 자료에서 Abstract 문단 내용과 dverse Events(or toxicity) 대해 설명하고 있는 모든 문단들을 가져와서 출력해줘. 텍스트 자료:{full_text}.",
                            },
                        ],
                    }
                ],
            )

            related_text_input = response_text.choices[0].message.content
            print("최종 사용할 논문 본문 내용:\n", related_text_input)
            return related_text_input

def tox_table_image(upload):
    if upload:
        base64_image = encode_image(upload.read())
        client = OpenAI()
        response_replic = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """

                            **해야하는 일 **
                            제공된 이미지에 있는 표를 텍스트 표로 바꿔서 csv format으로 반환해줘.
                            추가 설명은 주지 말고 CSV 포멧 표만 반환해.
                            이때, 표에 함께 있는 caption 글을 csv format 맨 밑에 행에 함께 반환해줘.
                            모든 정보를 다 담아야해. 누락하지마.

                            **고려할 것**
                            행/열을 잘 구분하고, 이때 **띄어쓰기나 볼드체 등의 특징**을 보고, **상위 개념 하위 개념** 관계를 모두 파악하여 상위항목(예를 들어 treat group name or 약물 복용 mg)-하위항목(grade 몇 번째인지)으로 **합쳐서 행**으로 만들어줘.

                            """,
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
        )

        response_replic = response_replic.choices[0].message.content

        rows111 = response_replic.split("\n")
        data111 = [row.split(",") for row in rows111]
        df111 = pd.DataFrame(data111)
        df111 = df111.applymap(lambda x: x.replace('"', '') if isinstance(x, str) else x)

        related_table_input = df111.to_csv(index=False)
        print("\n tox_table_image()에서 표 복제된 결과:",related_table_input)
    else:
            related_table_input = None
    return related_table_input

def tox_table(related_table_input, related_text_input):
    client = OpenAI()
    response_our_excel = client.chat.completions.create(
      model="gpt-4o",
      messages=[
          {
              "role": "user",
              "content": f"""
                You will be given a CSV table as input. 그것을 보고, 표의 행/열을 정확히 구분해서 수치에 대한 내용을 줄글로 모든 항목들을 설명해.
                그 다음 그 줄글을 이용해서 output data structure에 맞게 dataframe을 만들어줘.

                ### **Output Data Structure:**
                The output should be a new table with the following columns:
                ["treat group", "total no. patients", "adverse event", "event type", "AE Type", "grade group", "grade type", "patient (#)", "patient (%)", "dose reduction (%)", "dose discontinuation (%)", "dose interruption"]
                The table contains information about drug adverse events, including their grades, patient numbers, and percentages.
                Please organize the data such that every adverse event and every grade listed in the table is included in the output.
                No subgroup or category should be omitted.
                
                Data provided: {related_table_input}

                Text data provided: {related_text_input}. 만약 사용할 데이터가 없어도 열 헤더라도 만들어서 반환해.

                Especially, when you are working on the column of 'AE type', if the caption says 'drug-related', just write TRAE. If the adverse event occurs during treatment, write 'TRAE'; if it is not related to the drug, write 'TEAE'; if there is no information, write 'Unknown'.

                ## Instructions:
                1. Ensure every adverse event (e.g., diarrhea, rash, etc.) and every grade (e.g., G1, G2, All, etc.) is included in the output.
                2. If any data is missing for a column, explicitly write None.
                3. Maintain the exact formatting of symbols, parentheses, and numbers as shown in the original table.
                4. Return a well-structured table in CSV format, with all values accurately placed in their corresponding columns.
                5. Do not include any descriptions, explanations, or additional text in the output, only the table content.
                   하지만 한 가지 예외 사항이 있어. 만약, 텍스트 데이터를 사용한다면, 어떤 칸을 채우기 위해 텍스트 어느 부분을 사용했는지 알려줘.
                6. "total no. patients" 열의 내용을 쓸 때에는 수치만 적어. 예를 들어 "N=30" 이렇게 적지 말고, 30이라고 적어.
                7. 'event type' columns에는 adverse event의 값이 다음 옵션에서 해당하면 적어주고, 해당되지 않은 값은 빈칸으로 남겨줘. 옵션: Total, Diarrhea, Anemia, Constipation, Stomatitis, Acne, Pneumonia, Fatigue, Paronychia, Vomiting, Dyspnea, Headache, Rash, Nausea, Edema, AST increased, ALT increased, Hyperbilirubinemia, Neutropenia, Thrombocytopenia, Creatine phosphokinase increased, Palmar-Plantar Erythrodysesthesia (Hand-foot syndrome), Paresthesia, Cardiotoxicity
                8 'grade group' columns에는 제공받은 표에서의 grade 정보를 문자 그대로 가져오면 돼.
                9.'grade type' columns에는 grade group의 값이 다음 옵션에서 해당하면 적어주고, 해당되지 않은 값은 빈칸으로 남겨줘. 옵션: All, >=G3, <G3, G1, G2, G3, G4, G5 (G1부터 G5까지 있어.  >=G3은 G4, G5를 의미해. 부등호로 이해하면 돼.)
                Make sure the output table includes all subgroups and covers the entirety of the data provided without missing any details.

                가끔 표에 있는 정보를 누락해서 출력하는 경우가 있어. 절대 정보를 누락하지 말고, 정보를 모두 출력해. 빠진 행이 있는지 다시 점검해.
                """
          }
      ]
  )
    response_our_excel_data = response_our_excel.choices[0].message.content

    rows111 = response_our_excel_data.split("\n")
    data111 = [row.split(",") for row in rows111]
    df111 = pd.DataFrame(data111)
    df111 = df111.applymap(lambda x: x.replace('"', '') if isinstance(x, str) else x)

    header_idx = df111[df111[0] == 'treat group'].index[0]
    df111.columns = df111.iloc[header_idx].values
    df_cleaned = df111.iloc[header_idx + 1:].reset_index(drop=True)
    end_idx = df_cleaned[df_cleaned.iloc[:, 0].str.contains('```', na=False)].index[0]
    tox_output = df_cleaned.iloc[:end_idx].reset_index(drop=True)

    if 'treat group' in efficacy_output.columns:
        efficacy_output = efficacy_output.sort_values(by=['treat group'], ascending=[True]).reset_index(drop=True)

    print("Tox Ouput:")
    print(tox_output)

    return tox_output


def dose_pdf_to_text(upload):

    if upload is not None:
            file_bytes = upload.read()
            pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
            full_text = ""
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                full_text += page.get_text()

            client = OpenAI()
            response_text = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"제공한 텍스트 자료에서 Abstract 문단 내용과 Dose expansion(Dose Interruption, Dose Reduction, Dose Discontinuation)에 대해 설명하고 있는 모든 문단들을 가져와서 출력해줘. 텍스트 자료:{full_text}.",
                            },
                        ],
                    }
                ],
            )

            related_text_input = response_text.choices[0].message.content
            print("최종 사용할 논문 본문 내용:\n", related_text_input)
            return related_text_input

def dose_table_image(upload):
    if upload:
        base64_image = encode_image(upload.read())
        client = OpenAI()
        response_replic = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """

                        **해야하는 일 **
                        제공된 이미지에 있는 표를 텍스트 표로 바꿔서 csv format으로 반환해줘.
                        추가 설명은 주지 말고 CSV 포멧 표만 반환해.
                        이때, 표에 함께 있는 caption 글을 csv format 맨 밑에 행에 함께 반환해줘.

                        **고려할 것**
                        주로 복용 정보 혹은 total 정보가 treat_group에 들어갈 거고, Dose reduction, Dose discontinuation, Dose interruption의 내용 위주로 채우면 돼.
                        이때, dose escalation 정보와 dose expansion 정보가 같이 있을 수도 있어. 나는 dose expansion에 대한 정보만 필요하니까 그것만 가져와.
                        %값을 위주로 가져오면 돼.
                        행/열을 잘 구분하고, 이때 필요하다면 **띄어쓰기나 볼드체 등의 특징**을 보고, **상위 개념 하위 개념** 관계를 모두 파악하여 상위항목-하위항목으로 **합쳐서 행**으로 만들어줘.
                        """,
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )

        # print(response_middle.choices[0])
        response_replic = response_replic.choices[0].message.content
        #print('\n\n[STEP 2] 이미지에서 표 복제 text content:\n',response_replic)

        rows111 = response_replic.split("\n")
        data111 = [row.split(",") for row in rows111]
        df111 = pd.DataFrame(data111)
        df111 = df111.applymap(lambda x: x.replace('"', '') if isinstance(x, str) else x)
        #print("\n df111: ",df111)

        related_table_input = df111.to_csv(index=False)
        print("\n df_csv:",related_table_input)
    else:
            related_table_input = None
    return related_table_input

def dose_table(related_table_input, related_text_input):
    client = OpenAI()
    response_our_excel = client.chat.completions.create(
      model="gpt-4o",
      messages=[
          {
              "role": "user",
              "content": f"""
                I want to extract table data from the given csv format data and populate my dataframe with the required details.
                My DataFrame columns are: 
                ["treat group", "total no. patients", "adverse event", "event type", "AE Type", "grade group", "grade type", "patient (#)", "patient (%)", "dose reduction (%)", "dose discontinuation (%)", "dose interruption"]
                여기서  "dose reduction (%)", "dose discontinuation (%)", "dose interruption" 정보에 대해 테이블을 보고 기입하면 돼.

                Data provided: {related_table_input} 만약 사용할 데이터가 없어도 열 헤더라도 만들어서 반환해.

                Also, make sure to utilize the provided text data. If no tables are recognized, you can rely on the text data instead.
                Especially, when you are working on the column of 'AE type', if the caption says 'drug-related', just write TRAE. If the adverse event occurs during treatment, write TRAE; if it is not related to the drug, write TEAE; if there is no information, write Unknown.
                Text data: {related_text_input}

                ## Instructions:
                1. If any data is missing for a column, explicitly write None.
                2. Maintain the exact formatting of symbols, parentheses, and numbers as shown in the original table.
                3. Return a well-structured table in CSV format, with all values accurately placed in their corresponding columns.
                4. Do not include any descriptions, explanations, or additional text in the output, only the table content.
                Make sure the output table includes all subgroups and covers the entirety of the data provided without missing any details.
                """
          }
      ]
  )

    # prompt에 5-2) 나중에 후처리 때 처리해줘야함. 중간 csv만 빼오기.

    print(response_our_excel)
    response_our_excel_data = response_our_excel.choices[0].message.content

    rows111 = response_our_excel_data.split("\n")
    data111 = [row.split(",") for row in rows111]
    df111 = pd.DataFrame(data111)
    df111 = df111.applymap(lambda x: x.replace('"', '') if isinstance(x, str) else x)

    header_idx = df111[df111[0] == 'treat group'].index[0]
    df111.columns = df111.iloc[header_idx].values
    df_cleaned = df111.iloc[header_idx + 1:].reset_index(drop=True)
    end_idx = df_cleaned[df_cleaned.iloc[:, 0].str.contains('```', na=False)].index[0]
    dose_output = df_cleaned.iloc[:end_idx].reset_index(drop=True)
    print(dose_output)

    return dose_output

def tox_add_table(tox_table1=None, tox_table2=None, dose_table1=None):
    
    if tox_table1 is not None and tox_table2 is not None and dose_table1 is None: # tox table에 2개 인풋, dose에 없을 경우 && tox 1개 인풋, dose 1개 인풋
        

        tox_output = pd.concat([tox_table1, tox_table2], axis=0, ignore_index=True)
        print("tox_table1:")
        print(tox_table1)

        print("tox_table2:")
        print(tox_table2)
        
        print("final tox_output:")
        print(tox_output)

        return tox_output

    elif tox_table1 is not None and tox_table2 is not None and dose_table1 is not None: #tox table에 2개 인풋, dose에 있을 경우
        

        tox_output = pd.concat([tox_table1, tox_table2, dose_table1], axis=0, ignore_index=True)
        print("tox_table1:")
        print(tox_table1)

        print("tox_table2:")
        print(tox_table2)
        
        print("dose_output:")
        print(dose_table1)

        print("final_tox_output:")
        print(tox_output)

        return tox_output
    else:
        tox_output = None
        return None



## display setting... 
if paper_pdf_upload is None:
    st.warning('논문 PDF 파일을 업로드해주세요.', icon="⚠️")

else:
    # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    # folder_name = f"{timestamp}_[" + paper_pdf_upload.name.split('.')[0] + "]"
    # if not os.path.exists(folder_name):
    #     os.makedirs(folder_name)
    # diaplay_efficacy_excel_name =  f"./{folder_name}/efficacy_excel.xlsx"
    # diaplay_toxicity_excel_name =  f"./{folder_name}/toxicity_excel.xlsx"

    folder_name = paper_pdf_upload.name.split('.')[0]
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    diaplay_efficacy_excel_name = f"./{folder_name}/efficacy_excel.xlsx"
    diaplay_toxicity_excel_name = f"./{folder_name}/toxicity_excel.xlsx"
    diaplay_paper_name = f"./{folder_name}/paper.xlsx"

    with open(diaplay_paper_name, "wb") as f:
        f.write(paper_pdf_upload.getbuffer())

    def reset():
        st.session_state.key += 1

    with tab4:
        status_placeholder_left = st.empty()

        left, right = tab4.columns([1, 2])
        related_text_input = None

        with left:
            efficacy_run_button = st.button("자동 추출 실행", key="efficacy_run_button")
        
        with right:
            right_left, right_right = right.columns([1,1])
            reset_button = right_left.button('표 수정 초기화', on_click=reset, key="efficacy_reset_button")
            efficacy_save_button = right_right.button("최종 저장", key="efficacy_save_button")

        if efficacy_run_button:

            st.session_state.clear()

            if paper_pdf_upload is None and len(paper_efficacy_upload) == 0:
                st.warning("파일을 업로드해주세요!")

            else:
                if paper_pdf_upload is not None:  
                    st.toast('**[Step 1/3]** 논문을 읽고 있습니다...')
                    related_text_input = eff_pdf_to_text(upload=paper_pdf_upload)
                    st.toast('**[Step 1/3]** 논문 분석이 완료되었습니다!', icon="✅")
                else:
                    related_text_input = None
                    st.toast('**[Step 1/3]** 제공된 논문이 없어 이미지만 분석합니다.', icon="✅")

            if len(paper_efficacy_upload) >= 2:
                st.toast('**[Step 2/3]** 이미지 표를 분석 중입니다...')
                related_table_input1 = efficacy_table_image(upload=paper_efficacy_upload[0])
                related_table_input2 = efficacy_table_image(upload=paper_efficacy_upload[1])
                related_table_input1.to_excel(diaplay_efficacy_excel_name, index=False, engine='openpyxl')
                related_table_input2.to_excel(diaplay_efficacy_excel_name, index=False, engine='openpyxl')
                st.toast('**[Step 2/3]** 이미지 표 분석이 완료되었습니다!', icon="✅")

                st.toast('**[Step 3/3]** 최종 출력 표를 생성 중입니다...')
                efficacy_table_output1 = efficacy_table(related_table_input1, None) #원래는 (related_table_input1, related_text_input) 인데, 토큰 제한 걸릴까봐 우선 table만
                efficacy_table_output2 = efficacy_table(related_table_input2, None) #원래는 (related_table_input2, related_text_input) 인데, 토큰 제한 걸릴까봐 우선 table만
                efficacy_table_output = efficacy_add_table(efficacy_table_output1, efficacy_table_output2)
                efficacy_table_output.to_excel(diaplay_efficacy_excel_name, index=False, engine='openpyxl')
                st.toast('**[Step 3/3]** 최종 출력 표를 완성했습니다!', icon="🎉")
                
                status_placeholder_left.empty()

            elif len(paper_efficacy_upload) == 1:
                st.toast('**[Step 2/3]** 이미지 표를 분석 중입니다...')
                related_table_input = efficacy_table_image(upload=paper_efficacy_upload[0])
                related_table_input.to_excel(diaplay_efficacy_excel_name, index=False, engine='openpyxl')
                st.toast('**[Step 2/3]** 이미지 표 분석이 완료되었습니다!', icon="✅")

                st.toast('**[Step 3/3]** 최종 출력 표를 생성 중입니다...')
                efficacy_table_output = efficacy_table(related_table_input, None) #원래는 (related_table_input, related_text_input) 인데, 토큰 제한 걸릴까봐 우선 table만
                efficacy_table_output.to_excel(diaplay_efficacy_excel_name, index=False, engine='openpyxl')
                st.toast('**[Step 3/3]** 최종 출력 표를 완성했습니다!', icon="🎉")

                status_placeholder_left.empty()

            else:
                status_placeholder_left.markdown("Efficacy Table 이미지가 업로드되지 않았습니다. 우측의 출력 테이블은 오직 논문의 본문 내용에만 의존하여 생성됩니다.")
                st.toast('**[Step 2/2]** 최종 출력 표를 생성 중입니다...')
                efficacy_table_output = efficacy_table(None, related_text_input)
                efficacy_table_output.to_excel(diaplay_efficacy_excel_name, index=False, engine='openpyxl')
                st.toast('**[Step 2/2]** 최종 출력 표를 완성했습니다!', icon="🎉")
                status_placeholder_left.empty()

        ### Real display ...
        if 'eff_image_index' not in st.session_state:
            st.session_state.eff_image_index = 0

        if os.path.exists(diaplay_efficacy_excel_name):

            current_image = None
            if len(paper_efficacy_upload) >= 2:
                current_image_file = paper_efficacy_upload[st.session_state.eff_image_index]
                current_image = Image.open(current_image_file)

                left.write("**Original Table :camera: **")
                left.image(current_image, caption=f"Image {st.session_state.eff_image_index + 1} of {len(paper_efficacy_upload)}")

            elif len(paper_efficacy_upload) == 1:
                current_image_file = paper_efficacy_upload[st.session_state.eff_image_index]
                current_image = Image.open(current_image_file)
                left.write("**Original Table :camera:**")
                left.image(current_image)
            
            else:
                left.info("논문에서 다음 글을 이용하여 표를 구성했습니다. 틀릴 수 있으니 확인해주세요.")
                left.markdown(related_text_input)

            saved_df = pd.read_excel(diaplay_efficacy_excel_name, sheet_name=None)  # 모든 시트 읽기
            sheet_name = list(saved_df.keys())[0]  # 첫 번째 시트 이름
            saved_df[sheet_name].reset_index(inplace=True)

            unique_treat_group = saved_df[sheet_name]['treat_group'].nunique()
            unique_sub_group = saved_df[sheet_name]['sub_group'].nunique()
            unique_treat_group_values = saved_df[sheet_name]['treat_group'].unique()
            unique_sub_group_values = saved_df[sheet_name]['sub_group'].unique()
            effi_total_rows = len(saved_df[sheet_name])

            if current_image:
                image_height = current_image.size[1]
            else:
                image_height = 500
                
            if 'key' not in st.session_state:
                st.session_state.key = 0


            right.write("**Suggested Excel File :wrench:**")
            eff_edited_df = right.data_editor(saved_df[sheet_name], use_container_width=True, num_rows = "dynamic",  height=image_height, key=f'editor_{st.session_state.key}')
            st.info(f"""
                📢 **생성된 엑셀 표 수치 요약**
                    
                - 원본 테이블과 비교 후 많이 수정하거나 추가해야 한다면, 다시 **RUN** 해주세요.
                    
                - 분석 중 :red[종종 데이터가 누락되는 경우]가 있습니다. 자세히 수치를 살펴보시기 전에 **이미지 표의 행을 먼저 세고, 차이가 크면 RUN** 해주시면 효과적으로 사용하실 수 있습니다.

                | 항목               | 고유 값 개수   | 고유 값들                                  |
                |------------------|-------------|----------------------------------------|
                | **Treat group**   | {unique_treat_group}개  | {', '.join(map(str, unique_treat_group_values))}  |
                | **Sub group**     | {unique_sub_group}개  | {', '.join(map(str, unique_sub_group_values))}  |

                📊 **총 행의 개수**는 **{effi_total_rows}개**입니다.  

                ---

                📢 **간단히 수정하실 수 있다면, 참고해주세요.**  

                - **Value_type options:**
                **:gray-background[ORR]**, **:green-background[CR]**, **:orange-background[PR]**, **:red-background[DC]**, **:blue-background[SD]**, 
                **:orange-background[mPFS(m)]**, **:gray-background[OS(m)]**, **:violet-background[DoR(m)]**, **:blue-background[TTF(m)]**, **:green-background[i_ORR]**, 
                **:gray-background[i_CR]**, **:green-background[i_PR]**, **:gray-background[i_SD]**, **:red-background[i_mPFS (m)]**, **:violet-background[i_DoR (m)]**, 
                """
            )

        if efficacy_save_button:
            print("Tox edited df 817 line: ",eff_edited_df)
            if 'index' in eff_edited_df.columns:
                eff_edited_df = eff_edited_df.drop(columns=['index'])
            if 'level_0' in eff_edited_df.columns:
                eff_edited_df = eff_edited_df.drop(columns=['level_0']) 
            eff_edited_df.to_excel(diaplay_efficacy_excel_name, index=False, engine='openpyxl')
            st.toast(f"복제된 표는 '{diaplay_efficacy_excel_name}'에 저장되었습니다.")
            


    with tab5:

        status_placeholder_middle = st.empty()
        left2, right2 = tab5.columns([1, 2])

        with left2:
            toxicity_run_button = st.button("자동 추출 실행", key="toxicity_run_button")
        
        with right2:
            right2_left, right2_right = right2.columns([1,1])
            reset_button = right2_left.button('표 수정 초기화', on_click=reset, key="toxicity_reset_button")
            toxicity_save_button = right2_right.button("최종 저장", key="toxicity_save_button")

        if toxicity_run_button:

            st.session_state.clear()

            if paper_pdf_upload is None and len(paper_toxicity_upload) == 0 and len(paper_dose_upload) == 0 :
                st.warning("파일을 업로드해주세요!")

            else:
                if paper_pdf_upload is not None:  
                    st.toast('**[Step 1/3]** 논문을 읽고 있습니다...')
                    related_text_input = eff_pdf_to_text(upload=paper_pdf_upload)
                    st.toast('**[Step 1/3]** 논문 분석이 완료되었습니다!', icon="✅")

                else:
                    related_text_input = None
                    status_placeholder_middle.empty()
                    st.toast('**[Step 1/3]** 제공된 논문이 없어 이미지만 분석합니다.', icon="✅")

            
                # 조건 1: paper_toxicity_upload가 2개이고, paper_dose_upload가 없을 때
                if len(paper_toxicity_upload) >= 2 and len(paper_dose_upload) == 0:
                    st.toast('**[Step 2/3]** 이미지 표를 분석 중입니다...')
                    related_table_input1 = tox_table_image(upload=paper_toxicity_upload[0])
                    related_table_input2 = tox_table_image(upload=paper_toxicity_upload[1])
                    st.toast('**[Step 2/3]** 이미지 표 분석이 완료되었습니다!', icon="✅")

                    st.toast('**[Step 3/3]** 최종 출력 표를 생성 중입니다...')
                    tox_table_output1 = tox_table(related_table_input1, related_text_input)
                    tox_table_output2 = tox_table(related_table_input2, related_text_input)
                    
        
                    tox_table_output = tox_add_table(tox_table_output1, tox_table_output2)
                    tox_table_output.to_excel(diaplay_toxicity_excel_name, index=False, engine='openpyxl')
                    st.toast('**[Step 3/3]** 최종 출력 표를 완성했습니다!', icon="🎉")

                    status_placeholder_middle.empty()

                # 조건 2: paper_toxicity_upload가 1개이고, paper_dose_upload가 없을 때
                elif len(paper_toxicity_upload) == 1 and len(paper_dose_upload) == 0:
                    st.toast('**[Step 2/3]** 이미지 표를 분석 중입니다...')
                    related_table_input = tox_table_image(upload=paper_toxicity_upload[0])
                    st.toast('**[Step 2/3]** 이미지 표 분석이 완료되었습니다!', icon="✅")

                    st.toast('**[Step 3/3]** 최종 출력 표를 생성 중입니다...')
                    tox_table_output = tox_table(related_table_input, related_text_input)
        
                    tox_table_output.to_excel(diaplay_toxicity_excel_name, index=False, engine='openpyxl')
                    st.toast('**[Step 3/3]** 최종 출력 표를 완성했습니다!', icon="🎉")

                    status_placeholder_middle.empty()

                # 조건 3: paper_toxicity_upload가 없고, paper_dose_upload가 있을 때
                elif len(paper_toxicity_upload) == 0 and len(paper_dose_upload) == 1:
                    st.toast('**[Step 2/3]** 이미지 표를 분석 중입니다...')
                    related_table_input = dose_table_image(upload=paper_dose_upload[0])
                    st.toast('**[Step 2/3]** 이미지 표 분석이 완료되었습니다!', icon="✅")

                    st.toast('**[Step 3/3]** 최종 출력 표를 생성 중입니다...')
                    tox_table_output = dose_table(related_table_input, related_text_input)
                    
                    tox_table_output.to_excel(diaplay_toxicity_excel_name, index=False, engine='openpyxl')
                    st.toast('**[Step 3/3]** 최종 출력 표를 완성했습니다!', icon="🎉")

                    status_placeholder_middle.empty()

                # 조건 4: paper_toxicity_upload가 1개이고, paper_dose_upload가 있을 때
                elif len(paper_toxicity_upload) == 1 and len(paper_dose_upload) == 1:
                    st.toast('**[Step 2/3]** 이미지 표를 분석 중입니다...')
                    related_table_input1 = tox_table_image(upload=paper_toxicity_upload[0])
                    related_table_input2 = dose_table_image(upload=paper_dose_upload[0])
                    st.toast('**[Step 2/3]** 이미지 표 분석이 완료되었습니다!', icon="✅")

                    st.toast('**[Step 3/3]** 최종 출력 표를 생성 중입니다...')
                    tox_table_output1 = tox_table(related_table_input1, related_text_input)
                    tox_table_output2 = dose_table(related_table_input2, related_text_input)
                    tox_table_output = tox_add_table(tox_table_output1, tox_table_output2)
                                
                    tox_table_output.to_excel(diaplay_toxicity_excel_name, index=False, engine='openpyxl')
                    st.toast('**[Step 3/3]** 최종 출력 표를 완성했습니다!', icon="🎉")

                    status_placeholder_middle.empty()

                # 조건 5: paper_toxicity_upload가 2개이고, paper_dose_upload가 있을 때
                elif len(paper_toxicity_upload) == 2 and len(paper_dose_upload) == 1:
                    st.toast('**[Step 2/3]** 이미지 표를 분석 중입니다...')
                    related_table_input1 = tox_table_image(upload=paper_toxicity_upload[0])
                    related_table_input2 = tox_table_image(upload=paper_toxicity_upload[1])
                    related_table_input3 = dose_table_image(upload=paper_dose_upload[0])
                    st.toast('**[Step 2/3]** 이미지 표 분석이 완료되었습니다!', icon="✅")

                    st.toast('**[Step 3/3]** 최종 출력 표를 완성했습니다!', icon="🎉")
                    tox_table_output1 = tox_table(related_table_input1, related_text_input)
                    tox_table_output2 = tox_table(related_table_input2, related_text_input)
                    tox_table_output3 = dose_table(related_table_input3, related_text_input)
                    tox_table_output = tox_add_table(tox_table_output1, tox_table_output2, tox_table_output3)
                    
                    tox_table_output.to_excel(diaplay_toxicity_excel_name, index=False, engine='openpyxl')
                    st.toast('**[Step 3/3]** 최종 출력 표를 완성했습니다!', icon="🎉")

                    status_placeholder_middle.empty()

                # 그 외 다른 조건 (만약 조건에 맞지 않으면 여기로 들어옴)
                else:
                    status_placeholder_middle.markdown("Toxicity Table 이미지가 업로드되지 않았습니다. 우측의 출력 테이블은 오직 논문의 본문 내용에만 의존하여 생성됩니다.")
                    tox_table_output = tox_table(None, related_text_input)
                    tox_table_output.to_excel(diaplay_toxicity_excel_name, index=False, engine='openpyxl')
                    st.toast('**[Step 3/3]** 최종 출력 표를 완성했습니다!', icon="🎉")
                    
                    status_placeholder_middle.empty()


        if 'tox_image_index' not in st.session_state:
            st.session_state.tox_image_index = 0

        if 'dose_image_index' not in st.session_state:
            st.session_state.dose_image_index = 0

        if os.path.exists(diaplay_toxicity_excel_name):

            current_image = None
            if len(paper_toxicity_upload) >= 2:
                current_image_file = paper_toxicity_upload[st.session_state.tox_image_index]
                current_image = Image.open(current_image_file)

                left2.write("**Original Table :camera:**")
                left2.image(current_image, caption=f"Image {st.session_state.tox_image_index + 1} of {len(paper_toxicity_upload)}")
            
            elif len(paper_toxicity_upload) == 1:
                current_image_file = paper_toxicity_upload[st.session_state.tox_image_index]
                current_image = Image.open(current_image_file)
                left2.write("**Original Table :camera:**")
                left2.image(current_image)

            elif len(paper_dose_upload) >= 2:
                current_image_file = paper_dose_upload[st.session_state.tox_image_index]
                current_image = Image.open(current_image_file)

                left2.write("**Original Table :camera:**")
                left2.image(current_image, caption=f"원본 이미지: {st.session_state.dose_image_index + 1} of {len(paper_dose_upload)}")
            

            elif len(paper_dose_upload) == 1:
                current_image_file = paper_dose_upload[st.session_state.dose_image_index]
                current_image = Image.open(current_image_file)
                left2.write("**Original Table :camera:**")
                left2.image(current_image)

            elif len(paper_dose_upload) == 0 and len(paper_toxicity_upload) == 0:
                left2.info("논문에서 다음 글을 이용하여 표를 구성했습니다. 틀릴 수 있으니 확인해주세요.")
                left2.markdown(related_text_input)
            
            saved_df = pd.read_excel(diaplay_toxicity_excel_name, sheet_name=None)  # 모든 시트 읽기
            sheet_name = list(saved_df.keys())[0]  # 첫 번째 시트 이름
            saved_df[sheet_name].reset_index(inplace=True)

            unique_treat_group = saved_df[sheet_name]['treat group'].nunique()
            tox_total_rows = len(saved_df[sheet_name])
            unique_treat_group_values = saved_df[sheet_name]['treat group'].unique()

            if current_image:
                image_height = current_image.size[1]
            else:
                image_height = 500

            if 'key' not in st.session_state:
                st.session_state.key = 0

            right2.write("**Suggested Excel File :wrench:**")
            tox_edited_df = right2.data_editor(saved_df[sheet_name], use_container_width=True, num_rows = "dynamic", height = image_height,  key=f'editor2_{st.session_state.key}')
            st.info(f"""
                📢 **생성된 엑셀 표 수치 요약**
                    
                - 원본 테이블과 비교 후 많이 수정하거나 추가해야 한다면, 다시 **RUN** 해주세요.
                    
                - 분석 중 :red[종종 데이터가 누락되는 경우]가 있습니다. 자세히 수치를 살펴보시기 전에 **이미지 표의 행을 먼저 세고, 차이가 크면 RUN** 해주시면 효과적으로 사용하실 수 있습니다.

                | 항목               | 고유 값 개수   | 고유 값들                                  |
                |------------------|-------------|----------------------------------------|
                | **Treat group**   | {unique_treat_group}개  | {', '.join(map(str, unique_treat_group_values))}  |

                📊 **총 행의 개수**는 **{tox_total_rows}개**입니다.  

                ---

                📢 **간단히 수정하실 수 있다면, 참고해주세요.**  

                - **Event type options:**
                **:gray-background[Total]**, **:green-background[Diarrhea]**, **:orange-background[Anemia]**, **:red-background[Constipation]**, **:blue-background[Stomatitis]**, 
                **:orange-background[Dyspnea]**, **:gray-background[Headache]**, **:violet-background[Rash]**, **:blue-background[Nausea]**, **:green-background[Edema]**, 
                **:gray-background[AST increased]**, **:green-background[ALT increased]**, **:gray-background[Hyperbilirubinemia]**, **:red-background[Neutropenia]**, **:violet-background[Thrombocytopenia]**, 
                **:gray-background[Creatine phosphokinase increased]**, **:green-background[Palmar-Plantar Erythrodysesthesia (Hand-foot syndrome)]**, **:orange-background[Paresthesia]**, **:red-background[Cardiotoxicity]**
                
                - **Grade type options:**
                **:gray-background[All]**, **:green-background[>=G3]**, **:orange-background[<G3]**, **:violet-background[G1]**, **:blue-background[G2]**, **:orange-background[G3]**, **:red-background[G4]**, **:green-background[G5]**
                """




            )
        if toxicity_save_button:
            print("Tox edited df 817 line: ",tox_edited_df)
            if 'index' in tox_edited_df.columns:
                tox_edited_df = tox_edited_df.drop(columns=['index'])
            if 'level_0' in tox_edited_df.columns:
                tox_edited_df = tox_edited_df.drop(columns=['level_0']) 
            tox_edited_df.to_excel(diaplay_toxicity_excel_name, index=False, engine='openpyxl')
            st.toast(f"복제된 표는 '{diaplay_toxicity_excel_name}'에 저장되었습니다.")

    with tab1:
        st.info("""
                좌측 논문을 보고, 우측 표를 채워주세요. 완성되시면, 최종 저장 버튼을 통해 저장해주세요.
                    
                Demo 버전이라 크기 조정이 불가합니다. 추후 크기 조정이 가능하도록 구현할 예정입니다.
                """)
        tab1_left, tab1_right = tab1.columns([1,1])
        pdf_viewer(diaplay_paper_name, width=1000, height=1000)

        common_data = {
            "Drug": ["None", "None", "None"],
            "Drug_Synonym": ["None", "None", "None"],
            "Study Name": ["None", "None", "None"],
            "NCT no.": ["None", "None", "None"],
            "Reference / DOI": ["None", "None", "None"],
            "Reference / Link": ["None", "None", "None"],
            "Phase": ["None", "None", "None"],
            "Indication": ["None", "None", "None"],
            "Race / Ethnicity": ["None", "None", "None"],
        }
        common_df = pd.DataFrame(common_data)

        common_save_button = tab1_right.button("최종 저장", key="common_save_button")
        tab1_right.write("### Sheet1: Common table")
        common_edited_df = tab1_right.data_editor(common_df, use_container_width=True, num_rows="dynamic", key="common_edited_df")

        if common_save_button:
            diaplay_common_excel_name = f"./{folder_name}/common_excel.xlsx"
            common_edited_df.to_excel(diaplay_common_excel_name, index=False, engine='openpyxl')
            st.toast("f{diaplay_common_excel_name}에 저장되었습니다!")

    with tab2:
        treat_info_save_button = st.button("최종 저장", key="treat_info_save_button")
        treat_info_data = {
            "Treat_group": ["None", "None", "None"],
            "Drug": ["None", "None", "None"],
            "Dosing_type": ["None", "None", "None"],
            "Dosing_regimen": ["None", "None", "None"],
            "Dose(mg)": ["None", "None", "None"],
        }
        treat_info_df = pd.DataFrame(treat_info_data)
        st.write("### Sheet1: Treat_info table")
        treat_info_edited_df = st.data_editor(treat_info_df, use_container_width=True, num_rows="dynamic", key="treat_info_edited_df")

        if treat_info_save_button:
            diaplay_treat_info_excel_name = f"./{folder_name}/treat_info_excel.xlsx"
            treat_info_edited_df.to_excel(diaplay_treat_info_excel_name, index=False, engine='openpyxl')
            st.toast("f{diaplay_treat_info_excel_name}에 저장되었습니다!")

    with tab3:
        patient_info_save_button = st.button("최종 저장", key="patient_info_save_button")
        patient_info_data = {
            "Sub_group": ["None", "None", "None"],
            "Biomarker": ["None", "None", "None"],
            "No. patients": ["None", "None", "None"],
            "No. Prior systemic therapy": ["None", "None", "None"],
            "#": ["None", "None", "None"],
            "%": ["None", "None", "None"],
        }
        patient_info_df = pd.DataFrame(patient_info_data)
        st.write("### Sheet1: Patient_info table")
        patient_info_edited_df = st.data_editor(patient_info_df, use_container_width=True, num_rows="dynamic", key="patient_info_edited_df")

        if patient_info_save_button:
            diaplay_patient_info_excel_name = f"./{folder_name}/patient_info_excel.xlsx"
            patient_info_edited_df.to_excel(diaplay_patient_info_excel_name, index=False, engine='openpyxl')
            st.toast("f{diaplay_patient_info_excel_name}에 저장되었습니다!")


    with tab6:
        pk_common_save_button = st.button("최종 저장", key="pk_common_save_button")
        pk_common_data = {
            "Drug": ["None", "None", "None"],
            "Study Name": ["None", "None", "None"],
            "NCT no.": ["None", "None", "None"],
            "Reference / Link": ["None", "None", "None"],
        }
        pk_common_df = pd.DataFrame(pk_common_data)
        st.write("### Sheet2: PK Common table")
        pk_common_edited_df = st.data_editor(pk_common_df, use_container_width=True, num_rows="dynamic", key="pk_common_edited_df")

        if pk_common_save_button:
            diaplay_pk_common_excel_name = f"./{folder_name}/pk_common_excel.xlsx"
            pk_common_edited_df.to_excel(diaplay_pk_common_excel_name, index=False, engine='openpyxl')
            st.toast("f{diaplay_pk_common_excel_name}에 저장되었습니다!")

    with tab7:
        pk_dose_independent_save_button = st.button("최종 저장", key="pk_dose_independent_save_button")
        pk_dose_independent_data = {
            "Kpuu CSF": ["None", "None", "None"],
            "Human PPB (%)": ["None", "None", "None"],
            "Test item": ["None", "None", "None"],
            "IC50 [nM]": ["None", "None", "None"],
        }
        pk_dose_independent_df = pd.DataFrame(pk_dose_independent_data)
        st.write("### Sheet2: PK Dose independent table")
        pk_dose_independent_edited_df = st.data_editor(pk_dose_independent_df, use_container_width=True, num_rows="dynamic", key="pk_dose_independent_edited_df")

        if pk_dose_independent_save_button:
            diaplay_pk_dose_independent_excel_name = f"./{folder_name}/pk_dose_independent_excel.xlsx"
            pk_dose_independent_edited_df.to_excel(diaplay_pk_dose_independent_excel_name, index=False, engine='openpyxl')
            st.toast("f{diaplay_pk_dose_independent_excel_name}에 저장되었습니다!")

    with tab8:
        pk_dose_info_save_button = st.button("최종 저장", key="pk_dose_info_save_button")
        pk_dose_info_data = {
            "Dosing_type": ["None", "None", "None"],
            "Dosing_interval": ["None", "None", "None"],
            "Dose(mg)": ["None", "None", "None"],
            "Accumulation": ["None", "None", "None"],
            "Healthy": ["None", "None", "None"],
        }
        pk_dose_info_df = pd.DataFrame(pk_dose_info_data)
        st.write("### Sheet2: PK Dosing info table")
        pk_dose_info_edited_df = st.data_editor(pk_dose_info_df, use_container_width=True, num_rows="dynamic", key="pk_dose_info_edited_df")

        if pk_dose_info_save_button:
            diaplay_pk_dose_info_excel_name = f"./{folder_name}/pk_dose_info_excel.xlsx"
            pk_dose_info_edited_df.to_excel(diaplay_pk_dose_info_excel_name, index=False, engine='openpyxl')
            st.toast("f{diaplay_pk_dose_info_excel_name}에 저장되었습니다!")

    with tab9:
        pk_measure_save_button = st.button("최종 저장", key="pk_measure_save_button")
        pk_measure_data = {
            "Value_type": ["None", "None", "None"],
            "Value": ["None", "None", "None"],
            "Range_type": ["None", "None", "None"],
            "Range_low": ["None", "None", "None"],
            "Range_high": ["None", "None", "None"],
        }
        pk_measure_df = pd.DataFrame(pk_measure_data)
        st.write("### Sheet2: PK Measure info table")
        pk_measure_edited_df = st.data_editor(pk_measure_df, use_container_width=True, num_rows="dynamic", key="pk_measure_edited_df")

        if pk_measure_save_button:
            diaplay_pk_measure_excel_name = f"./{folder_name}/pk_measure_excel.xlsx"
            pk_measure_edited_df.to_excel(diaplay_pk_measure_excel_name, index=False, engine='openpyxl')
            st.toast("f{diaplay_pk_measure_excel_name}에 저장되었습니다!")