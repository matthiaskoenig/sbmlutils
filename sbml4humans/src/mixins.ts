import store from "@/store/index";

const browserStackMixin = {
    methods: {
        openComponent(pk: string): void {
            store.dispatch("pushToHistoryStack", pk);
        },
    },
};

export default {
    browserStackMixin,
};
