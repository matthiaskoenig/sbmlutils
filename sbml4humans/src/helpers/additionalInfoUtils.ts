import axios from "axios";
import urls from "@/data/urls";

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
