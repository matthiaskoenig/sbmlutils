function generateOMEXTree(OMEXRes: Record<string, unknown>): Record<string, unknown> {
    const manifest: Array<Record<string, string>> = (
        OMEXRes["manifest"] as Record<string, unknown>
    )["entries"] as Array<Record<string, string>>;

    const paths: Array<string> = [];
    manifest.forEach((item) => {
        paths.push(item["location"]);
    });

    const result: Array<Record<string, unknown>> = [];
    const level = { result };
    paths.forEach((path) => {
        path.split("/").reduce((r, name, i, a) => {
            if (!r[name]) {
                r[name] = { result: [] };
                r.result.push({ name, children: r[name].result });
            }

            return r[name];
        }, level);
    });

    const tree = result[0];
    console.log(tree);

    return tree;
}

export default {
    generateOMEXTree: generateOMEXTree,
};
