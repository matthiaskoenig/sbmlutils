/** Work in progress */

import store from "@/store/index";
import icons from "@/data/fontAwesome";
import colorScheme from "@/data/colorScheme";

import Katex from "@/components/layout/Katex.vue";
import BooleanSymbol from "@/components/layout/BooleanSymbol.vue";

const tableMixin = (listOfPKs: Array<string>): Record<string, unknown> => {
    const components = {
        katex: Katex,
        "boolean-symbol": BooleanSymbol,
    };

    const methods = {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    };

    const computed = {
        objects(): Array<Record<string, unknown>> {
            const listOfObjects: Array<Record<string, unknown>> = [];
            const allObjectsMap = store.state.allObjectsMap;

            (listOfPKs as unknown as Array<string>).forEach((pk) => {
                listOfObjects.push(allObjectsMap[pk]);
            });

            return listOfObjects;
        },

        color(): string {
            return colorScheme.componentColor["Parameter"];
        },

        icon(): string {
            return icons.icons["Parameter"];
        },
    };

    return {
        computed: computed,
        methods: methods,
        components: components,
    };
};

export default tableMixin;
