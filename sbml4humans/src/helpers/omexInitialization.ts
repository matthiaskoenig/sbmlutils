function comparator(a: Record<string, unknown>, b: Record<string, unknown>) {
    return (a["key"] as string).toLowerCase() < (b["key"] as string).toLowerCase()
        ? -1
        : (a["key"] as string).toLowerCase() > (b["key"] as string).toLowerCase()
        ? 1
        : 0;
}

function recursiveSort(tree: Record<string, unknown>): void {
    for (const i in tree["children"] as Array<Record<string, unknown>>) {
        const child = (tree["children"] as Array<Record<string, unknown>>)[i];
        recursiveSort(child);
    }
    if ((tree["children"] as Array<Record<string, unknown>>) === undefined) {
        return;
    } else {
        (tree["children"] as Array<Record<string, unknown>>).sort(comparator);
    }
}

function generateOMEXTree(OMEXRes: Record<string, unknown>): unknown {
    const manifest: Array<Record<string, string>> = (
        OMEXRes["manifest"] as Record<string, unknown>
    )["entries"] as Array<Record<string, string>>;

    const paths: Array<string> = [];
    const models: Array<string> = [];
    manifest.forEach((item) => {
        paths.push(item["location"]);

        if (item["format"].includes("sbml")) {
            const tokens = item["location"].split("/");
            models.push(tokens[tokens.length - 1]);
        }
    });

    const result: Array<Record<string, unknown>> = [];
    const level = { result };
    paths.forEach((path) => {
        path.split("/").reduce((r, label, i, a) => {
            if (!r[label]) {
                r[label] = { result: [] };
                if (r.result != null && models.includes(label)) {
                    r.result.push({
                        key: label,
                        label,
                        children: r[label].result,
                        type: "sbml",
                        data: path,
                    });
                } else if (r.result != null && label.includes(".")) {
                    // console.log(label);
                    r.result.push({
                        key: label,
                        label,
                        children: r[label].result,
                        icon: "pi pi-map",
                        type: "otherFiles",
                        data: path,
                    });
                } else if (r.result != null) {
                    r.result.push({
                        key: label,
                        label,
                        children: r[label].result,
                        icon: "pi pi-folder",
                        type: "folder",
                        data: path,
                    });
                }
            }

            return r[label];
        }, level);
    });

    const root = result[0];
    recursiveSort(root);

    const tree = {
        root: root["children"],
    };

    return tree;
}

export default {
    generateOMEXTree: generateOMEXTree,
};
