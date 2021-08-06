import axios from "axios";
import urls from "@/data/urls";

/*
Use abstraction layer for caching:

see for instance:

Use the following to cache the axios requests:
https://github.com/RasCarlito/axios-cache-adapter
https://www.npmjs.com/package/axios-cache-adapter

Some alternatives with similar patterns:
https://stackoverflow.com/questions/49671255/vue-js-cache-http-requests-with-axios
https://github.com/kuitos/axios-extensions#cacheadapterenhancer
 */



/**
 * Caching CVTerm/annotation information.
 * To avoid redundant web service queries information is cached in the front end.
 * @param additionalInfo
 * @param resourceID
 */
function cacheAdditionalInfo(
    additionalInfo: Record<string, unknown>,
    resourceID: string
) {
    if (localStorage.getItem("additionalInfo") == null) {
        localStorage.setItem("additionalInfo", JSON.stringify({}));
    }

    const localAdditionalInfo = JSON.parse(
        localStorage.getItem("additionalInfo") as string
    );

    localAdditionalInfo[resourceID] = additionalInfo;
    localStorage.setItem("additionalInfo", JSON.stringify(localAdditionalInfo));
}

async function queryAdditionalInfoForResource(resourceID: string) {
    const QUERY_URL = urls.API_BASE_URL + urls.RESOURCE_INFO_URL + resourceID;

    await axios.get(QUERY_URL).then((res) => {
        const data = res.data;

        const additionalInfo = data;
        cacheAdditionalInfo(additionalInfo, resourceID);
    });
}

function getCachedAdditionalInfo(resourceID: string) {
    if (localStorage.getItem("additionalInfo") == null) {
        return null;
    }

    const localAdditionalInfo = JSON.parse(
        localStorage.getItem("additionalInfo") as string
    );

    return localAdditionalInfo[resourceID];
}

async function getAdditionalInfo(resourceID: string): Promise<Record<string, unknown>> {
    let cachedInfo = getCachedAdditionalInfo(resourceID);
    if (cachedInfo != undefined) {
        return cachedInfo;
    }

    await queryAdditionalInfoForResource(resourceID); // let the information cache
    cachedInfo = getCachedAdditionalInfo(resourceID);
    return cachedInfo;
}

export default {
    getAdditionalInfo: getAdditionalInfo,
};
