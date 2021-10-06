import axios from "axios";
import { VUE_APP_APIURL } from "@/store";
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
export async function fetchAdditionalInfo(
    resourceID: string
): Promise<Record<string, unknown>> {
    const QUERY_URL =
        VUE_APP_APIURL +
        "/annotation_resource?resource=" +
        encodeURIComponent(resourceID);
    let res = api({
        url: QUERY_URL,
        method: "get",
    }).then((response) => {
        res = response.data;
        return res;
    });
    return res;
}

// eslint-disable-next-line @typescript-eslint/explicit-module-boundary-types
export function checkAPIResponse(response: any): void {
    if (response.data["errors"]) {
        alert(
            "An error occurred. Please report this on\n" +
                "https://github.com/matthiaskoenig/sbmlutils/issues/new\n" +
                "so we can improve the service.\n\n" +
                JSON.stringify(response.data, null, 1)
        );
    }
}
