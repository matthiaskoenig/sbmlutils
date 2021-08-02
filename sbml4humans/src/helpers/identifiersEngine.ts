import axios from "axios";
import urls from "@/data/urls";

function getRegistryDataset(): Record<string, unknown> {
    axios.get(urls.DATASET_URL).then((res) => {
        return res.data.payload;
    });
    return {
        error: "Dataset not available",
    };
}

function getIdentifierData(identifier: string): Record<string, unknown> {
    const dataset = getRegistryDataset();

    if (dataset.error) {
        return {};
    }
    return dataset[identifier] as Record<string, unknown>;
}

function getTermAndDescription(data: Record<string, unknown>): Record<string, unknown> {
    const res = {};
    res["name"] = data["name"];
    res["description"] = data["description"];

    res["resources"] = [];
    (data["resources"] as Array<Record<string, unknown>>).forEach((resource) => {
        const resourceObject = {
            name: resource.name,
            description: resource.description,
            urlPattern: resource.urlPattern,
        };

        res["resources"].push(resourceObject);
    });

    return res;
}

export default {
    getRegistryDataset,
    getIdentifierData,
    getTermAndDescription,
};
