# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import json
import unittest

from parameterized import parameterized_class

from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.models import DagBag, DagRun
from airflow.models.serialized_dag import SerializedDagModel
from airflow.settings import Session
from airflow.www import app as application
from tests.test_utils.config import conf_vars


@parameterized_class([
    {"dag_serialzation": "False"},
    {"dag_serialzation": "True"},
])
class TestDagRunsEndpoint(unittest.TestCase):
    dag_serialzation = "False"

    @classmethod
    def setUpClass(cls):
        super(TestDagRunsEndpoint, cls).setUpClass()
        session = Session()
        session.query(DagRun).delete()
        session.commit()
        session.close()
        dagbag = DagBag(include_examples=True)
        for dag in dagbag.dags.values():
            dag.sync_to_db()
            SerializedDagModel.write_dag(dag)

    def setUp(self):
        super(TestDagRunsEndpoint, self).setUp()
        app = application.create_app(testing=True)
        self.app = app.test_client()

    def tearDown(self):
        session = Session()
        session.query(DagRun).delete()
        session.commit()
        session.close()
        super(TestDagRunsEndpoint, self).tearDown()

    def test_get_dag_runs_success(self):
        with conf_vars(
            {("core", "store_serialized_dags"): self.dag_serialzation}
        ):
            url_template = '/api/experimental/dags/{}/dag_runs'
            dag_id = 'example_bash_operator'
            # Create DagRun
            dag_run = trigger_dag(
                dag_id=dag_id, run_id='test_get_dag_runs_success')

            response = self.app.get(url_template.format(dag_id))
            self.assertEqual(200, response.status_code)
            data = json.loads(response.data.decode('utf-8'))

            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['dag_id'], dag_id)
            self.assertEqual(data[0]['id'], dag_run.id)

    def test_get_dag_runs_success_with_state_parameter(self):
        with conf_vars(
            {("core", "store_serialized_dags"): self.dag_serialzation}
        ):
            url_template = '/api/experimental/dags/{}/dag_runs?state=running'
            dag_id = 'example_bash_operator'
            # Create DagRun
            dag_run = trigger_dag(
                dag_id=dag_id, run_id='test_get_dag_runs_success')

            response = self.app.get(url_template.format(dag_id))
            self.assertEqual(200, response.status_code)
            data = json.loads(response.data.decode('utf-8'))

            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['dag_id'], dag_id)
            self.assertEqual(data[0]['id'], dag_run.id)

    def test_get_dag_runs_success_with_capital_state_parameter(self):
        with conf_vars(
            {("core", "store_serialized_dags"): self.dag_serialzation}
        ):
            url_template = '/api/experimental/dags/{}/dag_runs?state=RUNNING'
            dag_id = 'example_bash_operator'
            # Create DagRun
            dag_run = trigger_dag(
                dag_id=dag_id, run_id='test_get_dag_runs_success')

            response = self.app.get(url_template.format(dag_id))
            self.assertEqual(200, response.status_code)
            data = json.loads(response.data.decode('utf-8'))

            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['dag_id'], dag_id)
            self.assertEqual(data[0]['id'], dag_run.id)

    def test_get_dag_runs_success_with_state_no_result(self):
        with conf_vars(
            {("core", "store_serialized_dags"): self.dag_serialzation}
        ):
            url_template = '/api/experimental/dags/{}/dag_runs?state=dummy'
            dag_id = 'example_bash_operator'
            # Create DagRun
            trigger_dag(dag_id=dag_id, run_id='test_get_dag_runs_success')

            response = self.app.get(url_template.format(dag_id))
            self.assertEqual(200, response.status_code)
            data = json.loads(response.data.decode('utf-8'))

            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 0)

    def test_get_dag_runs_invalid_dag_id(self):
        with conf_vars(
            {("core", "store_serialized_dags"): self.dag_serialzation}
        ):
            url_template = '/api/experimental/dags/{}/dag_runs'
            dag_id = 'DUMMY_DAG'

            response = self.app.get(url_template.format(dag_id))
            self.assertEqual(400, response.status_code)
            data = json.loads(response.data.decode('utf-8'))

            self.assertNotIsInstance(data, list)

    def test_get_dag_runs_no_runs(self):
        with conf_vars(
            {("core", "store_serialized_dags"): self.dag_serialzation}
        ):
            url_template = '/api/experimental/dags/{}/dag_runs'
            dag_id = 'example_bash_operator'

            response = self.app.get(url_template.format(dag_id))
            self.assertEqual(200, response.status_code)
            data = json.loads(response.data.decode('utf-8'))

            self.assertIsInstance(data, list)
            self.assertEqual(len(data), 0)

    def test_get_dag_runs_with_dagrun_id_filter(self):
        url_template = '/api/experimental/dags/{}/dag_runs?dagrun_id=1'
        dag_id = 'example_bash_operator'
        # Create DagRun
        dag_run = trigger_dag(dag_id=dag_id, run_id='1')

        response = self.app.get(url_template.format(dag_id))
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data.decode('utf-8'))

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['dag_id'], dag_id)
        self.assertEqual(data[0]['id'], dag_run.id)

    def test_get_dag_runs_with_unmatched_dagrun_id_filter(self):
        url_template = '/api/experimental/dags/{}/dag_runs?dagrun_id=2'
        dag_id = 'example_bash_operator'
        # Create DagRun
        dag_run = trigger_dag(dag_id=dag_id, run_id='1')

        response = self.app.get(url_template.format(dag_id))
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data.decode('utf-8'))

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)


if __name__ == '__main__':
    unittest.main()
