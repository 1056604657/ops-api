from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from httpx import AsyncClient

app = FastAPI()

# 用于存储Cookie信息的全局变量
cookie_value = "isg=BD4-Sl5b1ae_DgHWVaxm8WA5jVKAfwL5ZCF-_uhHygF8i91lUA84CFAtA9dHqPoR; tfstk=fKxxpUwhXYexV2eSDPglsVu6Ao-ADhp4eIJQj1f05QdJ1Q7gmiAgXUdMwx5MCjR9X_OBoPjjQAd9d_-Mo10qXAI2qEqGijS9CBbttXmnxKJV0GMotURtCNsCB1a_ss97FnVvbNmnxKJff2ODkDxDzfMlt1s1lGs7P_WFhGaf5YC5B9z_GCO6FYBOQ1ZfCZi5VOX1f1O1fYpWsilON-1gXFqEiUpUaar_fnsNk9QbSlrw2tQYuK1RETxRHZCdzBM7NHpBhHW9bvaO6sTXRitt95bJNETCchhLN18cLgWBtBEhsWfdIrHJfPzNlTrJApLHKuwkFTCnHcUa7akPe6D-ePzNyyWRtxnT7P7rU; EGG_SESS=NQTUV5FRyJ8wRsJGPf4sK9ixC77AGX-EQJdGiQXtVK4hgc5p8IvKUsbiCLmiW_C10VPm3ujMjhhaQFZ2IDp6nfXhv70zWsIuyr8maqBBBEuU0wfYphZeE9NyxblGozv86-FOFxbX7cqsuy6T46-pCmoFijTYgMOiTSK9UY6C4PhqP6DcpdUtgdH0yKAa9BQs2ct5rYRO4pCglVUsrhuoKWNs1CqXwU067y9xeGFgc-OTU0tP5q0BGL4j9HYvk-o7PqguK_NLrwoIG5-G_BpslQOC56JkUlZUo0-CAhuvtMhqWJg2nXNPzucGxWR3uHtYFAyssIi0honBKAHi9_nqvRSkDPibxaVcXOkY1f5NNxLKAMg42m-cD2R_QPCIDlA1NWyfdvmWprT13H1MzK4HBRONUaX8g1flpO5SG0JmgamUn_g1Myoiev5CEAuBcmcP-CU5x7VkIROjc2T_TmEXjPMc1bL0jrU1xZYSau5UoP81n9ljrXmXEXEqNitICbopRxNB4REBlx5LxjvuAH-tr_GAxDtPkMtbtay4uaZ_Qnmq9jcHROwZ5PiOMKwYXQK-TldPDVm9Vtu3UXOCovRxHfWnJZoHRaWAFaBwf-xT6I8OHxduZLHncOugWV3Gs1ORYtI5yWmwRssJ42iO02ly9pL-c8UwvTJBwkNkskTKbXRDno1sNN9lCyYjxAQ9T6RyoIH32ZjxKUzeQcXnF79CGPs09OMhDDaEv5UD_aOP3JkuI2qZfrOL2aEU4_PFVThdZzGMjeZYxN_xl6OQHvqJqEvkgPjkJqVYaNvOWKsPI0pVq9kH45SRiY9nni6dMkNTBtcPhRKDFmz9c6pD0fmhY-8ZPZyWIzQdlyb07TPEr-zmxmKz7PGWi0_oj1D9Pq2kPDtedaR28uYGrc1c8y8-YOsbRlx_8-oKs9SOFeC7gieDanVLeURKSWqXAWGLr_O-_v-zlQn6xwIEAWCvIZaHPUaI5qeQHyx9B3ptKk-yUsfeqmKgTbZgoKsBbci0tu6znhv72CJQRu0JiW_0lHghWfssUBpCJwTy6nOaQ8gbqabPVp8fIpa9vngGIBjUU7K-ThvYdH4amAKO7jAfun_vbdf_bSj3Nw7vL_voYRfImnZJjmQIYvZetn9bFJI38sn4jvlabxdtVneeT6Qs_a3NTeOasUT7_YGF2yYxL3FfVlljuuuk7-hX_PpxcuTo5rRSkgAP9QtxSREH6JTaSruzkFboYSjVEu-aG2ZrNtN7Hj1VkC4LL9bhJlQl1bcSI_bE1qNJyKOlr7IaoWUmYMZx6zwsLN1HGiw8e5mAnzFavjhrzp5suryakQ_d2oUfRds9XS4Vy1u97qvXjdzhwnBs0v5WZapq1rv0Ljy_jDMwE8ixHyjkxtypyECAPhS7m_sxJaXOm5kjChA-mmTurYq5p6AgxwBkOl4yJHz3Vs_w6Ug9P6jIu7YzHS1YhOGXzJzFO0in_hDvJG2AQSwU1Tx_XfXdjkG-oJ7bv77-AfeaPIPB1AJBMLluNMeb5dqbt5GGBJCpeNjfDF5ZDO9i6tfv5w==; gray_auth=2; oauth_state=7f0c087c46038659f352b283d87636a4; passport_login=MTE2ODU5MDgsaGlzbWFydGNhcix1ZnhiYWY1d25kemE1Y201dXljeXhjajducmZ2dWE3bywxNzMzMTk2NzI2LE1EWXlZbVpqTkdJM1l6QTRaR1ptWXpFME1USm1ZbUl4TkdKalpXWXhZV1k9; xlly_s=1; dev_help=3eb7UTyWiHoDUf7P8IxanzMxNzRiN2Y0Zjk2MDFhYWZkMTJjNTVmYTkwNzAzYWEyZjA2MDM1NTFhM2I4MWEyMGM4NmU1YzFiYzA3ZjA2Yja3cw7sm0akcq7bWCP41yEJulvhi23MUwCdTmyPFbusojsn7ATSHX08olirNGI%2BVsWZjPXzzBdETpxH8QKCQQIqpK3PtfD1SB%2FiGtf0HVrmwEaNCcxpdy5MOSp1xPWLi8U%3D; ctoken=zSJrgIiMI0gHk_YKvIxb90jZ; guid=9f1e-bb36-570d-4858; cna=GzuiH2TIgTACATohxSqLf91v"


# 设置Cookie的接口
@app.post("/set-cookie/")
async def set_cookie(cookie: str):
    print(123)
    global cookie_value
    cookie_value = cookie
    return {"message": "Cookie has been set"}


# 转发请求的接口
@app.get("/forward/")
async def forward_request(request: Request):
    global cookie_value

    if not cookie_value:
        raise HTTPException(status_code=400, detail="Cookie is not set")

    url = "https://console.amap.com/api/dev/flow/key/list"
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "bx-v": "2.5.22",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://console.amap.com/dev/flow/detail",
        "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "cookie": cookie_value,
    }

    print("发送请求到URL:", url)
    

    async with AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            print("响应状态码:", response.status_code)
            print("响应内容:", response.text)
            
            if response.status_code != 200:
                return JSONResponse(
                    status_code=response.status_code,
                    content={
                        "message": "Failed to retrieve data",
                        "status_code": response.status_code,
                        "response": response.text,
                        "used_cookie": cookie_value
                    }
                )

            return JSONResponse(status_code=response.status_code, content=response.json())
        except Exception as e:
            print("请求发生错误:", str(e))
            return JSONResponse(
                status_code=500,
                content={"message": f"Request failed: {str(e)}"}
            )

# 查询历史数据的接口
@app.get("/history/")
async def get_history(
        uri: str, x_type: int = 0, time_type: int = 0, key: str = "", pid: int = 10100
):
    global cookie_value

    if not cookie_value:
        raise HTTPException(status_code=400, detail="Cookie is not set")

    url = f"https://console.amap.com/api/dev/flow/flow-detail?uri={uri}&x_type={x_type}&time_type={time_type}&key={key}&pid={pid}"
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "bx-v": "2.5.22",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://console.amap.com/dev/flow/detail",
        "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
        "cookie": cookie_value,
    }

    async with AsyncClient() as client:
        response = await client.get(url, headers=headers)

    if response.status_code != 200:
        return JSONResponse(status_code=response.status_code, content={"message": "Failed to retrieve data"})

    return JSONResponse(status_code=response.status_code, content=response.json())