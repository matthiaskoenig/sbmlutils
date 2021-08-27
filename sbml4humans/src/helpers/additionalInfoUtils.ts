import axios from "axios";
import urls from "@/data/urls";
import { setupCache } from "axios-cache-adapter";

const cache = setupCache({
    maxAge: 15 * 60 * 1000,
});

const api = axios.create({
    adapter: cache.adapter,
});

/**
 * Caching CVTerm/annotation information.
 * To avoid redundant web service queries information is cached in the front end.
 * @param additionalInfo
 * @param resourceID
 */
async function fetchAdditionalInfo(
    resourceID: string
): Promise<Record<string, unknown>> {
    //return { "bruh": "bruh" };
    const QUERY_URL = urls.API_BASE_URL + urls.RESOURCE_INFO_URL + resourceID;
    let res = api({
        url: QUERY_URL,
        method: "get",
    }).then((response) => {
        res = response.data;
        return res;
    });
    return res;
}

export default {
    fetchAdditionalInfo: fetchAdditionalInfo,
};
