import axios from "axios";
import urls from "@/data/urls";
// import { setupCache } from "axios-cache-adapter";

// const cache = setupCache({
//     maxAge: 15 * 60 * 1000,
// });

const api = axios.create({
    //adapter: cache.adapter,  // activate for caching
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
    const QUERY_URL =
        urls.API_BASE_URL +
        "/annotation_resource?resource=" +
        encodeURIComponent(resourceID);
    console.log(QUERY_URL);
    let res = api({
        url: QUERY_URL,
        method: "get",
    }).then((response) => {
        res = response.data;
        return res;
    });
    return res;
}

function checkAPIResponse(response){
    if (response.data["errors"]){
        alert(
            "An error occurred. Please report this on\n" +
            "https://github.com/matthiaskoenig/sbmlutils/issues/new\n" +
            "so we can improve the service.\n\n" +
            JSON.stringify(response.data, null, 1)
        );
    }
    return null;
};


export default {
    fetchAdditionalInfo: fetchAdditionalInfo,
    checkAPIResponse: checkAPIResponse,
};
